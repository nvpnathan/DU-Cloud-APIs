import os
import mimetypes
import requests
import pstats
import cProfile
from dotenv import load_dotenv

load_dotenv()

document_folder = "./"

base_url = os.environ['BASE_URL']
projectId = os.environ['PROJECT_ID']
# extractorId = os.environ['EXTRACTOR_ID']

# Auth
client_id = os.environ['APP_ID']
client_secret = os.environ['APP_SECRET']
token_url = os.environ['AUTH_URL']


# Authentication
def get_bearer_token(client_id, client_secret, token_url):
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
        'scope': 'Du.DocumentManager.Document Du.Classification.Api Du.Digitization.Api Du.Extraction.Api Du.Validation.Api'
    }

    try:
        # Make the POST request to obtain the token
        response = requests.post(token_url, data=data)
        response.raise_for_status()  # Raise an exception for HTTP errors

        token_data = response.json()
        
        # Extract and return the access token
        access_token = token_data.get('access_token')
        if access_token:
            print("Authenticated!\n")
            return access_token
        else:
            print("Error: No access token received")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching token: {e}")
        return None


bearer_token = get_bearer_token(client_id, client_secret, token_url)
# if bearer_token:
#     print("Bearer Token:", bearer_token)


# Digitize Document
def digitize_document(base_url, projectId, document_path, bearer_token):
    # Define the API endpoint for digitization
    api_url = f"{base_url}{projectId}/digitization/start?api-version=1"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "accept": "text/plain"
    }    

    try:
        # Get Document mime type
        mime_type, _ = mimetypes.guess_type(document_path)
        # If the MIME type couldn't be guessed, default to 'application/octet-stream'
        if mime_type is None:
            mime_type = 'application/octet-stream'

        # Open the file
        files = {'File': (document_path, open(document_path, 'rb'), mime_type)}
        # Make the POST request with files parameter
        response = requests.post(api_url, files=files, headers=headers)

        # Check if the request was successful (status code 200)
        if response.status_code == 202:
            print("Document successfully digitized!")
            response_data = response.json()
            # Extract the documentID if it exists
            document_id = response_data.get('documentId')
            if document_id:
                print(f"Document ID: {document_id}\n")
                return document_id
        else:
            print(f"Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"An error occurred: {e}")


# Classify Document
def classify_document(base_url, projectId, document_id, bearer_token):
    # Define the API endpoint for document classification
    api_url = f"{base_url}{projectId}/classifiers/ml-classification/classification?api-version=1"

    # Define the headers with the Bearer token and content type
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "accept": "text/plain",
        "Content-Type": "application/json"
    }

    data = {
        "documentId": f"{document_id}"
    }

    try:
        # Make the POST request
        response = requests.post(api_url, json=data, headers=headers)

        if response.status_code == 200:
            print("Document successfully classified!")
            # Try parsing the JSON response
            try:
                classificationResults = response.json()
                document_type_id = None
                for result in classificationResults['classificationResults']:
                    if result['DocumentId'] == document_id:
                        document_type_id = result['DocumentTypeId']
                        classification_confidence = result['Confidence']
                        break

                if document_type_id:
                    print(f"Document Type ID: {document_type_id}, Confidence: {classification_confidence}\n")
                else:
                    print("Document ID not found in classification results.")

                return document_type_id
            except ValueError as ve:
                print(f"Error parsing JSON response: {ve}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"An error occurred during classification: {e}")


# Extract Document Data
def extract_document(base_url, projectId, extractorId, document_id, bearer_token):
    # Define the API endpoint for document extraction
    api_url = f"{base_url}{projectId}/extractors/{extractorId}/extraction?api-version=1"

    # Define the headers with the Bearer token and content type
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "accept": "text/plain",
        "Content-Type": "application/json"
    }

    data = {
        "documentId": f"{document_id}",
        "prompts": None
    }

    try:
        # Make the POST request
        response = requests.post(api_url, json=data, headers=headers)

        if response.status_code == 200:
            print("Document successfully extracted!\n")
            # Try parsing the JSON response
            try:
                extracted_data = response.json()
                return extracted_data
            except ValueError as ve:
                print(f"Error parsing JSON response: {ve}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"An error occurred during extraction: {e}")


# Print Extracted Results
def get_extraction_results(extraction_results):
    field_data = {}

    for field in extraction_results['extractionResult']['ResultsDocument']['Fields']:
       if isinstance(field, dict):  # Ensure 'field' is a dictionary
        field_name = field.get('FieldName')
        values = [value.get('Value') for value in field.get('Values', [])]

        confidence = None
        if 'Values' in field and field['Values'] and 'Confidence' in field['Values'][0]:
            confidence = field['Values'][0]['Confidence']
        if field_name:
            field_data[field_name] = {'values': values, 'Confidence': confidence}

    # Print parsed data
    print("Extraction Results: \n")
    for field_name, data in field_data.items():
        values = data['values']
        confidence = data.get('Confidence')
        print(f"{field_name}: {values}, Confidence: {confidence}")


# Main function to process documents in the folder
def process_documents_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(('.png',' .jpe', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.pdf' )):  # Filter for supported file types
            document_path = os.path.join(folder_path, filename)
            print(f"Processing document: {document_path}")
            bearer_token = get_bearer_token(client_id, client_secret, token_url)
            if bearer_token:
                document_id = digitize_document(base_url, projectId, document_path, bearer_token)
                if document_id:
                    extractorId = classify_document(base_url, projectId, document_id, bearer_token)
                    if extractorId:
                        extraction_results = extract_document(base_url, projectId, extractorId, document_id, bearer_token)
                        if extraction_results:
                            get_extraction_results(extraction_results)

# Call the main function to process documents in the specified folder
process_documents_in_folder(document_folder)


### Analytic purposes ###
# cProfile.run('process_documents_in_folder(document_folder)', 'profile_stats')

# # Analyze the profiling results
# stats = pstats.Stats('profile_stats')
# stats.strip_dirs()
# stats.sort_stats('cumulative')  # Sort by cumulative time spent in functions
# stats.print_stats(10)  # Print the top 10 functions by cumulative time
