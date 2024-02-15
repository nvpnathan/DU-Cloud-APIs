import requests


class Validate:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def validate_extraction_results(self, extractor_id, document_id, extraction_results):
        # Define the API endpoint for validation
        api_url = f"{self.base_url}{self.project_id}/extractors/{extractor_id}/validation/start?api-version=1"

        # Define the headers with the Bearer token and content type
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "text/plain",
            "Content-Type": "application/json"
        }

        # Define the payload data
        payload = {
            "documentId": document_id,
            "actionTitle": f"Validate - {extractor_id}",
            "actionPriority": "Medium",
            "actionCatalog": "default_du_actions",
            "actionFolder": "Shared",
            "storageBucketName": "du_storage_bucket",
            "storageBucketDirectoryPath": "du_storage_bucket",
            "extractionResult": extraction_results['extractionResult']
        }

        try:
            # Make the POST request
            response = requests.post(api_url, json=payload, headers=headers)

            if response.status_code == 202:
                print("Validation request successfully sent!")
                # Parse the JSON response
                response_data = response.json()
                # Extract and return the operationId
                operation_id = response_data.get("operationId")
                return operation_id
            else:
                print(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"An error occurred during validation: {e}")
