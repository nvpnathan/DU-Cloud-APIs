import os
import concurrent.futures
from discovery import Discovery
from digitize import Digitize
from classify import Classify
from extract import Extract
from validate import Validate
from write_results import WriteResults
from auth import initialize_authentication
from config import (
    load_env_file,
    load_endpoints,
    load_prompts,
    ensure_database,
    get_processing_config,
)
from config import ProcessingConfig, DocumentProcessingContext

# Initialize/Verify DB
ensure_database()
# Load environment variables
load_env_file()
base_url = os.getenv("BASE_URL")

# Initialize Authentication
auth = initialize_authentication()
bearer_token = auth.bearer_token
discovery_client = Discovery(base_url, bearer_token)


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
    config: ProcessingConfig,
    context: DocumentProcessingContext,
) -> None:
    """Process a document using the provided configuration and context."""
    try:
        document_id = start_digitization(document_path)

        # Perform classification if required
        document_type_id = (
            classify_document(document_id, document_path, config, context)
            if config.perform_classification
            else None
        )

        # Perform extraction if required
        if config.perform_extraction:
            # Extractor handling
            extractor_id, extractor_name = get_extractor(context, document_type_id)
            if extractor_id and extractor_name:
                perform_extraction(
                    document_id,
                    document_path,
                    extractor_id,
                    extractor_name,
                    config,
                )

    except Exception as e:
        print(f"Error processing {document_path}: {e}")


# 1. Digitization function
def start_digitization(document_path: str) -> str:
    return digitize_client.digitize(document_path)


# 2. Classification function
def classify_document(
    document_id: str,
    document_path: str,
    config: ProcessingConfig,
    context: DocumentProcessingContext,
) -> str | None:
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
    if config.validate_classification:
        document_type_id = validate_client.validate_classification_results(
            document_id,
            context.classifier,
            document_type_id,
            classification_prompts,
        )

    return document_type_id


# 3. Extractor handling function
def get_extractor(
    context: DocumentProcessingContext,
    document_type_id: str | None,
) -> tuple[str | None, str | None]:
    if document_type_id:
        extractor_id = context.extractor_dict.get(document_type_id, {}).get("id")
        extractor_name = context.extractor_dict.get(document_type_id, {}).get("name")
    else:
        extractor_info = next(iter(context.extractor_dict.values()))
        extractor_id = extractor_info.get("id")
        extractor_name = extractor_info.get("name")

    generative_extractor = context.extractor_dict.get("generative_extractor")
    if generative_extractor and document_type_id in generative_extractor.get(
        "doc_type_ids", []
    ):
        extractor_id = "generative_extractor"
        extractor_name = document_type_id
    if generative_extractor and not document_type_id:
        extractor_id = "generative_extractor"
        extractor_name = "default_doc"

    print_extractor_log(extractor_id, extractor_name, document_type_id)
    return extractor_id, extractor_name


def print_extractor_log(
    extractor_id: str | None, extractor_name: str | None, document_type_id: str | None
) -> None:
    if extractor_id:
        print(f"Using {extractor_id} for document type {extractor_name}")
    else:
        print(f"No extractor found for document type {document_type_id}")


# 4. Perform extraction function
def perform_extraction(
    document_id: str,
    document_path: str,
    extractor_id: str,
    extractor_name: str,
    config: ProcessingConfig,
) -> None:
    extraction_prompts = (
        load_prompts(extractor_name) if extractor_id == "generative_extractor" else None
    )
    extraction_results = extract_client.extract_document(
        extractor_id, document_id, extraction_prompts
    )

    if not config.validate_extraction:
        write_extraction_results(extraction_results, document_path)
    else:
        validated_results = validate_client.validate_extraction_results(
            extractor_id, document_id, extraction_results, extraction_prompts
        )
        if validated_results:
            write_validated_results(
                validated_results, extraction_results, document_path
            )


def write_extraction_results(extraction_results, document_path):
    write_results = WriteResults(
        document_path=document_path, extraction_results=extraction_results
    )
    write_results.write_results()


def write_validated_results(validated_results, extraction_results, document_path):
    write_results = WriteResults(
        document_path=document_path,
        extraction_results=extraction_results,
        validation_extraction_results=validated_results,
    )
    write_results.write_results()


# Main function to process documents in the folder
def process_documents_in_folder(
    folder_path: str,
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

    # Initialize ProcessingConfig using Discovery's cache or prompts
    config = get_processing_config(discovery_client)

    print("Configuration loaded:")
    print("Validate Classification:", config.validate_classification)
    print("Validate Extraction:", config.validate_extraction)
    print("Perform Classification:", config.perform_classification)
    print("Perform Extraction:", config.perform_extraction)

    # Load context
    project_id, classifier, extractor_dict = load_endpoints(
        discovery_client=discovery_client,
        load_classifier=config.perform_classification,
        load_extractor=config.perform_extraction,
    )
    context = DocumentProcessingContext(project_id, classifier, extractor_dict)
    # Initialize clients using the context
    digitize_client, classify_client, extract_client, validate_client = (
        initialize_clients(context, base_url, bearer_token)
    )

    # Process documents
    process_documents_in_folder(DOCUMENT_FOLDER, config, context)
