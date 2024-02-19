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
def process_documents_in_folder(folder_path, validate_document=False):
    for filename in os.listdir(folder_path):
        if filename.endswith(('.png', '.jpe', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.pdf')):
            document_path = os.path.join(folder_path, filename)
            print(f"Processing document: {document_path}")
            try:
                document_id = digitize_client.start(document_path)
                if document_id:
                    document_type_id = classify_client.classify_document(document_id)
                    if document_type_id:
                        extraction_results = extract_client.extract_document(document_type_id, document_id)
                        if not validate_document:
                            CSVWriter.write_extraction_results_to_csv(extraction_results, document_path)
                            CSVWriter.pprint_csv_results(document_path)
                        else:
                            validated_results = validate_client.validate_extraction_results(document_type_id, document_id, extraction_results)
                            if validated_results:
                                CSVWriter.write_validated_results_to_csv(validated_results, extraction_results, document_path)
                                CSVWriter.pprint_csv_results(document_path)
            except Exception as e:
                print(f"Error processing {document_path}: {e}")


# Call the main function to process documents in the specified folder
if __name__ == "__main__":
    document_folder = "./Example Documents"
    process_documents_in_folder(document_folder, validate_document=False)
