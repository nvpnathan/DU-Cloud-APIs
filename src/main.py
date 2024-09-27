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


def load_endpoints():
    discovery_client = Discovery(base_url, bearer_token)
    project_id = discovery_client.get_projects()
    classifier = discovery_client.get_classifers(project_id)
    extractor_dict = discovery_client.get_extractors(project_id)

    return project_id, classifier, extractor_dict


project_id, classifier, extractor_dict = load_endpoints()

digitize_client = Digitize(base_url, project_id, bearer_token)
classify_client = Classify(base_url, project_id, bearer_token)
extract_client = Extract(base_url, project_id, bearer_token)
validate_client = Validate(base_url, project_id, bearer_token)


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
    validate_classification: bool,
    validate_extraction: bool,
    generative_classification: bool,
    generative_extraction: bool,
) -> None:
    """Process a document by digitizing, classifying, and extracting information.

    Args:
        document_path (str): The path to the document to be processed.
        output_directory (str): The directory where the output will be saved.
        validate_classification (bool): Flag indicating whether to validate the document classification.
        validate_extraction (bool): Flag indicating whether to validate the document extraction.
        generative_classification (bool): Flag indicating whether to use generative classification.
        generative_extraction (bool): Flag indicating whether to use generative extraction.

    Returns:
        None

    Raises:
        Exception: If any error occurs during the document processing.
    """
    try:
        # Start the digitization process for the document
        document_id = digitize_client.digitize(document_path)
        if document_id:
            classification_prompts = (
                load_prompts("classification") if generative_classification else None
            )
            # Classify the document to obtain its type
            document_type_id = classify_client.classify_document(
                document_id,
                classifier,
                classification_prompts,
                validate_classification,
            )

            # Handle classification validation based on flags
            if validate_classification and document_type_id:
                classification_results = (
                    validate_client.validate_classification_results(
                        document_id,
                        classifier,
                        document_type_id,
                        classification_prompts,
                    )
                )
                extractor_id = extractor_dict[classification_results]["id"]
                extractor_name = extractor_dict[classification_results]["name"]
            else:
                extractor_id = extractor_dict[document_type_id]["id"]
                extractor_name = extractor_dict[document_type_id]["name"]

            # Handle extraction based on validation flags
            if extractor_id:
                extraction_prompts = (
                    load_prompts(extractor_name) if generative_extraction else None
                )
                extractor_id = (
                    "generative_extractor" if generative_extraction else extractor_id
                )
                extraction_results = extract_client.extract_document(
                    extractor_id, document_id, extraction_prompts
                )

                # Write extraction results based on validation flag
                if not validate_extraction:
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
        # Handle any errors that occur during the document processing
        print(f"Error processing {document_path}: {e}")


# Main function to process documents in the folder
def process_documents_in_folder(
    folder_path: str,
    output_directory: str,
    validate_classification: bool = False,
    validate_extraction: bool = False,
    generative_classification: bool = False,
    generative_extraction: bool = False,
) -> None:
    """Process all documents in a folder.

    Args:
        folder_path (str): The path to the folder containing documents to be processed.
        output_directory (str): The directory where the output will be saved.
        validate_classification (bool): Flag indicating whether to validate document classification.
        validate_extraction (bool): Flag indicating whether to validate document extraction.
        generative_classification (bool): Flag indicating whether to use generative classification.
        generative_extraction (bool): Flag indicating whether to use generative extraction.

    Returns:
        None
    """

    for filename in os.listdir(folder_path):
        if filename.endswith(
            (".png", ".jpe", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".pdf")
        ):
            document_path = os.path.join(folder_path, filename)
            print(f"Processing document: {document_path}")
            process_document(
                document_path,
                output_directory,
                validate_classification,
                validate_extraction,
                generative_classification,
                generative_extraction,
            )


# Call the main function to process documents in the specified folder
if __name__ == "__main__":
    DOCUMENT_FOLDER = "./example_documents"
    OUTPUT_DIRECTORY = "./output_results"
    process_documents_in_folder(
        DOCUMENT_FOLDER,
        OUTPUT_DIRECTORY,
        validate_classification=False,
        validate_extraction=False,
    )
