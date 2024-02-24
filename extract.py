import requests


class Extract:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def extract_document(self, extractor_id, document_id, prompts=None):
        # Define the API endpoint for document extraction
        api_url = f"{self.base_url}{self.project_id}/extractors/{extractor_id}/extraction?api-version=1"

        # Define the headers with the Bearer token and content type
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "text/plain",
            "Content-Type": "application/json"
        }

        data = {
            "documentId": f"{document_id}",
            **(prompts or {})
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
