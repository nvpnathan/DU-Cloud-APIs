import os
import json
from dotenv import load_dotenv
from auth import Authentication
from discovery import Discovery
from digitize import Digitize
from classify import Classify
from extract import Extract
from validate import Validate
from result_utils import CSVWriter
from config import ProcessingConfig, DocumentProcessingContext

# Load environment variables
load_dotenv()

# Initialize Authentication
auth = Authentication(
    os.environ["APP_ID"], os.environ["APP_SECRET"], os.environ["AUTH_URL"]
)
bearer_token = auth.get_bearer_token()

# Initialize API clients
base_url = os.environ["BASE_URL"]
# project_id = os.environ["PROJECT_ID"]


def load_endpoints(load_classifier, load_extractor):
    discovery_client = Discovery(base_url, bearer_token)
    project_id = discovery_client.get_projects()

    # Conditionally load classifiers and extractors based on flags
    classifier = (
        discovery_client.get_classifers(project_id) if load_classifier else None
    )
    extractor_dict = (
        discovery_client.get_extractors(project_id) if load_extractor else None
    )

    return project_id, classifier, extractor_dict


# Function to initialize clients
def initialize_clients(
    context: DocumentProcessingContext, base_url: str, bearer_token: str
):
    digitize_client = Digitize(base_url, context.project_id, bearer_token)
    classify_client = Classify(base_url, context.project_id, bearer_token)
    extract_client = Extract(base_url, context.project_id, bearer_token)
    validate_client = Validate(base_url, context.project_id, bearer_token)

    return digitize_client, classify_client, extract_client, validate_client


# Function to load prompts from a JSON file based on the document type ID
def load_prompts(document_type_id: str) -> dict | None:
    prompts_directory = "generative_prompts"
    prompts_file = os.path.join(prompts_directory, f"{document_type_id}_prompts.json")
    if os.path.exists(prompts_file):
        with open(prompts_file, "r", encoding="utf-8") as file:
            return json.load(file)
    else:
        print(f"Error: File '{prompts_file}' not found.")
        return None


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
                document_id,
                context.classifier,
                classification_prompts,
                config.validate_classification,
            )
            extractor_id = context.extractor_dict[document_type_id]["id"]
            extractor_name = context.extractor_dict[document_type_id]["name"]

            if config.validate_classification and document_type_id:
                classification_results = (
                    validate_client.validate_classification_results(
                        document_id,
                        context.classifier,
                        document_type_id,
                        classification_prompts,
                    )
                )
                extractor_id = context.extractor_dict[classification_results]["id"]
                extractor_name = context.extractor_dict[classification_results]["name"]
        else:
            extractor_info = next(iter(context.extractor_dict.values()))
            extractor_id = extractor_info.get("id")
            extractor_name = extractor_info.get("name")

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
                    classification_results,
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
    for filename in os.listdir(folder_path):
        if filename.endswith(
            (".png", ".jpe", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".pdf")
        ):
            document_path = os.path.join(folder_path, filename)
            print(f"Processing document: {document_path}")
            process_document(document_path, output_directory, config, context)


if __name__ == "__main__":
    DOCUMENT_FOLDER = "./example_documents"
    OUTPUT_DIRECTORY = "./output_results"

    # Create a configuration object
    config = ProcessingConfig(
        validate_classification=False,
        validate_extraction=False,
        perform_classification=True,
        perform_extraction=True,
    )

    # Load context
    project_id, classifier, extractor_dict = load_endpoints(
        load_classifier=config.perform_classification,
        load_extractor=config.perform_extraction,
    )
    context = DocumentProcessingContext(project_id, classifier, extractor_dict)
    # Initialize clients using the context
    digitize_client, classify_client, extract_client, validate_client = (
        initialize_clients(context, base_url, bearer_token)
    )

    # Process documents
    process_documents_in_folder(DOCUMENT_FOLDER, OUTPUT_DIRECTORY, config, context)
