import requests
import mimetypes


class Digitize:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def start(self, document_path):
        # Define the API endpoint for digitization
        api_url = f"{self.base_url}{self.project_id}/digitization/start?api-version=1"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
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