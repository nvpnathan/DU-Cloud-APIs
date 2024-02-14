import os
import mimetypes
import pstats
import cProfile
import requests
from dotenv import load_dotenv

load_dotenv()

document_path = "ID Card.jpg"


base_url = os.environ['BASE_URL']
projectId = os.environ['PROJECT_ID']
extractorId = os.environ['EXTRACTOR_ID']

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
            print("Authenticated")
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
    

# Extract Document Data
def extract_document(base_url, project_id, document_path, bearer_token):
    # Digitize the document first
    document_id = digitize_document(base_url, project_id, document_path, bearer_token)
    
    if document_id:
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
            # Make the GET request
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

    # Return None if an error occurs during digitization, extraction, or parsing
    return None

# Print Extracted Results
def get_extraction_results():
    extraction_results = extract_document(base_url, projectId, document_path, bearer_token)
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


get_extraction_results()


### Analytic purposes ###
# cProfile.run('get_extraction_results()', 'profile_stats')

# # Analyze the profiling results
# stats = pstats.Stats('profile_stats')
# stats.strip_dirs()
# stats.sort_stats('cumulative')  # Sort by cumulative time spent in functions
# stats.print_stats(10)  # Print the top 10 functions by cumulative time
