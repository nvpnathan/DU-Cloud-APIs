import os
import concurrent.futures
from dotenv import load_dotenv
from digitize import Digitize
from classify import Classify
from extract import Extract
from validate import Validate
from result_utils import CSVWriter
from auth import initialize_authentication
from config import load_endpoints, load_prompts
from config import ProcessingConfig, DocumentProcessingContext

# Load environment variables
load_dotenv()
base_url = os.environ["BASE_URL"]

# Initialize Authentication
auth = initialize_authentication()
bearer_token = auth.bearer_token


# Function to initialize clients
def initialize_clients(
    context: DocumentProcessingContext, base_url: str, bearer_token: str
):
    digitize_client = Digitize(base_url, context.project_id, bearer_token)
    classify_client = Classify(base_url, context.project_id, bearer_token)
    extract_client = Extract(base_url, context.project_id, bearer_token)
    validate_client = Validate(base_url, context.project_id, bearer_token)

    return digitize_client, classify_client, extract_client, validate_client


# Function to handle document processing
def process_document(
    document_path: str,
    output_directory: str,
    config: ProcessingConfig,
    context: DocumentProcessingContext,
) -> None:
    """Process a document using the provided configuration and context.

    Args:
        document_path (str): Path to the document to be processed.
        output_directory (str): Directory where output will be saved.
        config (ProcessingConfig): Configuration for validation, classification, and extraction.
        context (DocumentProcessingContext): Contains project_id, classifier, and extractor_dict.
    """
    try:
        # Start digitization process
        document_id = digitize_client.digitize(document_path)

        if document_id and config.perform_classification:
            classification_prompts = (
                load_prompts("classification")
                if context.classifier == "generative_classifier"
                else None
            )
            document_type_id = classify_client.classify_document(
                document_path,
                document_id,
                context.classifier,
                classification_prompts,
                config.validate_classification,
            )

        if config.validate_classification and document_type_id:
            classification_results = validate_client.validate_classification_results(
                document_id,
                context.classifier,
                document_type_id,
                classification_prompts,
            )

            # Default extractor settings
            extractor_id = context.extractor_dict.get(classification_results, {}).get(
                "id"
            )
            extractor_name = context.extractor_dict.get(classification_results, {}).get(
                "name"
            )

            # Check if the generative extractor is available
            generative_extractor = context.extractor_dict.get("generative_extractor")

            # If the generative extractor exists and the document type matches
            if (
                generative_extractor
                and classification_results
                in generative_extractor.get("doc_type_ids", [])
            ):
                extractor_id = "generative_extractor"
                extractor_name = classification_results

            # Log or handle the result if extractor_id is not found
            if extractor_id:
                print(f"Using {extractor_id} for document type {extractor_name}")
            else:
                print(f"No extractor found for document type {classification_results}")

        if config.perform_extraction:
            # Default extractor settings
            if not extractor_id:
                extractor_id = context.extractor_dict.get(document_type_id, {}).get(
                    "id"
                )
                extractor_name = context.extractor_dict.get(document_type_id, {}).get(
                    "name"
                )

            # Check if the generative extractor is available
            generative_extractor = context.extractor_dict.get("generative_extractor")

            # If the generative extractor exists and the document type matches
            if generative_extractor and document_type_id in generative_extractor.get(
                "doc_type_ids", []
            ):
                extractor_id = "generative_extractor"
                extractor_name = document_type_id

            # Log or handle the result if extractor_id is not found
            if extractor_id:
                print(f"Using {extractor_id} for document type {extractor_name}")
            else:
                print(f"No extractor found for document type {document_type_id}")

        if config.perform_extraction and extractor_id:
            extraction_prompts = (
                load_prompts(extractor_name)
                if extractor_id == "generative_extractor"
                else None
            )
            extraction_results = extract_client.extract_document(
                extractor_id, document_id, extraction_prompts
            )

            if not config.validate_extraction:
                CSVWriter.write_extraction_results_to_csv(
                    extraction_results, document_path, output_directory
                )
                CSVWriter.pprint_csv_results(document_path, output_directory)
            else:
                validated_results = validate_client.validate_extraction_results(
                    extractor_id,
                    document_id,
                    extraction_results,
                    extraction_prompts,
                )
                if validated_results:
                    CSVWriter.write_validated_results_to_csv(
                        validated_results,
                        extraction_results,
                        document_path,
                        output_directory,
                    )
                    CSVWriter.pprint_csv_results(document_path, output_directory)
    except Exception as e:
        print(f"Error processing {document_path}: {e}")


# Main function to process documents in the folder
def process_documents_in_folder(
    folder_path: str,
    output_directory: str,
    config: ProcessingConfig,
    context: DocumentProcessingContext,
) -> None:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []

        for filename in os.listdir(folder_path):
            if filename.lower().endswith(
                (".png", ".jpe", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".pdf")
            ):
                document_path = os.path.join(folder_path, filename)
                print(f"Submitting document for processing: {document_path}")
                # Submit the document processing function to the thread pool
                futures.append(
                    executor.submit(
                        process_document,
                        document_path,
                        output_directory,
                        config,
                        context,
                    )
                )

        # Wait for all threads to complete and optionally handle the results
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()  # This will raise an exception if the thread failed
            except Exception as e:
                print(f"Error in thread execution: {e}")


if __name__ == "__main__":
    DOCUMENT_FOLDER = "./example_documents"
    OUTPUT_DIRECTORY = "./output_results"

    # Create a configuration object
    config = ProcessingConfig(
        validate_classification=True,
        validate_extraction=False,
        perform_classification=True,
        perform_extraction=True,
    )

    # Load context
    project_id, classifier, extractor_dict = load_endpoints(
        load_classifier=config.perform_classification,
        load_extractor=config.perform_extraction,
        base_url=os.environ["BASE_URL"],
        bearer_token=bearer_token,
    )
    context = DocumentProcessingContext(project_id, classifier, extractor_dict)
    # Initialize clients using the context
    digitize_client, classify_client, extract_client, validate_client = (
        initialize_clients(context, base_url, bearer_token)
    )

    # Process documents
    process_documents_in_folder(DOCUMENT_FOLDER, OUTPUT_DIRECTORY, config, context)
