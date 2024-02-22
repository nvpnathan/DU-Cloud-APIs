import os
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


# Main function to process documents in the folder
def process_documents_in_folder(folder_path, validate_classification=False, validate_extraction=False, 
                                generative_classification=False, generative_extraction=False):
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
                    if generative_classification:
                        document_type_id = classify_client.classify_document(document_id, validate_classification, classifier='generative_classifier', prompts=classify_prompts)
                    else:
                        document_type_id = classify_client.classify_document(document_id, validate_classification)
                    if validate_classification:
                        # If classification validation is enabled, validate the classification results
                        classification_results = validate_client.validate_classification_results(document_id, document_type_id)
                        if document_type_id:
                            # Extract information from the document based on the classification results
                            extraction_results = extract_client.extract_document(classification_results, document_id)
                            if not validate_extraction:
                                # If extraction validation is disabled, write the extraction results to CSV
                                CSVWriter.write_extraction_results_to_csv(extraction_results, document_path)
                                CSVWriter.pprint_csv_results(document_path)
                            else:
                                # Validate the extraction results and write the validated results to CSV
                                validated_results = validate_client.validate_extraction_results(document_type_id, document_id, extraction_results)
                                if validated_results:
                                    CSVWriter.write_validated_results_to_csv(validated_results, extraction_results, document_path)
                                    CSVWriter.pprint_csv_results(document_path)
                    else:
                        # If classification validation is disabled, directly use the obtained document type ID
                        classification_results = document_type_id
                        if document_type_id:
                            # Extract information from the document based on the document type ID
                            extraction_results = extract_client.extract_document(classification_results, document_id)
                            if not validate_extraction:
                                # If extraction validation is disabled, write the extraction results to CSV
                                CSVWriter.write_extraction_results_to_csv(extraction_results, document_path)
                                CSVWriter.pprint_csv_results(document_path)
                            else:
                                # Validate the extraction results and write the validated results to CSV
                                validated_results = validate_client.validate_extraction_results(document_type_id, document_id, extraction_results)
                                if validated_results:
                                    CSVWriter.write_validated_results_to_csv(validated_results, extraction_results, document_path)
                                    CSVWriter.pprint_csv_results(document_path)
            except Exception as e:
                # Handle any errors that occur during the document processing
                print(f"Error processing {document_path}: {e}")


# Call the main function to process documents in the specified folder
if __name__ == "__main__":
    document_folder = "./Example Documents"
    # Specify whether to perform classification and extraction validation
    process_documents_in_folder(document_folder, validate_classification=False, validate_extraction=False, 
                                generative_classification=False, generative_extraction=False)