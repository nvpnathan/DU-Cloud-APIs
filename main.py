import os
import json
from dotenv import load_dotenv
from auth import Authentication
from digitize import Digitize
from classify import Classify
from extract import Extract
from validate import Validate
from result_utils import CSVWriter

# Load environment variables
load_dotenv()

# Initialize Authentication
auth = Authentication(os.environ['APP_ID'], os.environ['APP_SECRET'], os.environ['AUTH_URL'])
bearer_token = auth.get_bearer_token()

# Initialize API clients
base_url = os.environ['BASE_URL']
project_id = os.environ['PROJECT_ID']
digitize_client = Digitize(base_url, project_id, bearer_token)
classify_client = Classify(base_url, project_id, bearer_token)
extract_client = Extract(base_url, project_id, bearer_token)
validate_client = Validate(base_url, project_id, bearer_token)

# Function to load prompts from a JSON file based on the document type ID
def load_prompts(document_type_id):
    prompts_directory = "Generative Prompts"
    prompts_file = os.path.join(prompts_directory, f"{document_type_id}_prompts.json")
    if os.path.exists(prompts_file):
        with open(prompts_file, "r") as file:
            prompts = json.load(file)
        return prompts
    else:
        print(f"Error: File '{prompts_file}' not found.")
        return None

# Main function to process documents in the folder
def process_documents_in_folder(folder_path, output_directory, validate_classification=False, validate_extraction=False, 
                                generative_classification=False, generative_extraction=False):
    # Load classification prompts if generative_classification is enabled
    classifier_id = 'generative_classifier' if generative_classification else 'ml-classification'
    classification_prompts = load_prompts('classification') if generative_classification else None

    # Iterate through files in the specified folder
    for filename in os.listdir(folder_path):
        # Check if the file has one of the supported extensions
        if filename.endswith(('.png', '.jpe', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.pdf')):
            # Construct the full path of the document
            document_path = os.path.join(folder_path, filename)
            print(f"Processing document: {document_path}")
            try:
                # Start the digitization process for the document
                document_id = digitize_client.start(document_path)
                if document_id:
                    # Classify the document to obtain its type
                    document_type_id = classify_client.classify_document(document_id, classifier_id, classification_prompts, validate_classification)
                    if validate_classification:
                        # If classification validation is enabled, validate the classification results
                        classification_results = validate_client.validate_classification_results(document_id, classifier_id, document_type_id, classification_prompts)
                        if document_type_id:
                            # Load extraction prompts based on the document type ID
                            extraction_prompts = load_prompts(classification_results) if generative_extraction else None
                            classification_results = 'generative_extractor' if generative_extraction else classification_results
                            # Extract information from the document based on the classification results
                            extraction_results = extract_client.extract_document(classification_results, document_id, extraction_prompts)
                            if not validate_extraction:
                                # If extraction validation is disabled, write the extraction results to CSV
                                CSVWriter.write_extraction_results_to_csv(extraction_results, document_path, output_directory)
                                CSVWriter.pprint_csv_results(document_path)
                            else:
                                # Validate the extraction results and write the validated results to CSV
                                validated_results = validate_client.validate_extraction_results(classification_results, document_id, extraction_results, extraction_prompts)
                                if validated_results:
                                    CSVWriter.write_validated_results_to_csv(validated_results, extraction_results, document_path, output_directory)
                                    CSVWriter.pprint_csv_results(document_path)
                    else:
                        # If classification validation is disabled, directly use the obtained document type ID
                        classification_results = document_type_id
                        if classification_results:
                            # Load extraction prompts based on the document type ID
                            extraction_prompts = load_prompts(document_type_id) if generative_extraction else None
                            classification_results = 'generative_extractor' if generative_extraction else classification_results
                            # Extract information from the document based on the document type ID
                            extraction_results = extract_client.extract_document(classification_results, document_id, extraction_prompts)
                            if not validate_extraction:
                                # If extraction validation is disabled, write the extraction results to CSV
                                CSVWriter.write_extraction_results_to_csv(extraction_results, document_path, output_directory)
                                CSVWriter.pprint_csv_results(document_path)
                            else:
                                # Validate the extraction results and write the validated results to CSV
                                validated_results = validate_client.validate_extraction_results(classification_results, document_id, extraction_results, extraction_prompts)
                                if validated_results:
                                    CSVWriter.write_validated_results_to_csv(validated_results, extraction_results, document_path, output_directory)
                                    CSVWriter.pprint_csv_results(document_path)
            except Exception as e:
                # Handle any errors that occur during the document processing
                print(f"Error processing {document_path}: {e}")


# Call the main function to process documents in the specified folder
if __name__ == "__main__":
    document_folder = "./Example Documents"
    output_directory= "./Output Results"
    # Specify whether to perform classification and extraction validation
    process_documents_in_folder(document_folder, output_directory, validate_classification=False, validate_extraction=True, 
                                generative_classification=False, generative_extraction=True)
