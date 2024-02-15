import time
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
            # Make the POST request to initiate validation
            response = requests.post(api_url, json=payload, headers=headers)

            if response.status_code == 202:
                print("\nValidation request sent!")
                # Parse the JSON response
                response_data = response.json()
                # Extract and return the operationId
                operation_id = response_data.get("operationId")
                
                # Wait until the validation operation is completed
                validation_result = self.submit_validation_request(extractor_id, operation_id)
                return validation_result
            else:
                print(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"An error occurred during validation: {e}")


    def submit_validation_request(self, extractor_id, operation_id):
        url = f'{self.base_url}{self.project_id}/extractors/{extractor_id}/validation/result/{operation_id}?api-version=1'
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }

        while True:
            response = requests.get(url, headers=headers)
            response_data = response.json()
            if response_data['status'] == 'Succeeded':
                print("Validation request submitted successfully!")
                while True:
                    response = requests.get(url, headers=headers)
                    response_data = response.json()
                    # Check the status inside actionData
                    action_data_status = response_data['result']['actionData']['status']
                    print(f"Validate Document Extraction action status: {action_data_status}")
                    if action_data_status == 'Unassigned':
                        print("Validation Document Extraction is unassigned. Waiting...")
                    elif action_data_status == 'Pending':
                        print("Validate Document Extraction in progress. Waiting...")
                    elif action_data_status == 'Completed':
                        print("Validate Document Extraction is completed.")
                        return response_data
                    else:
                        print("Unknown validation action status.")
                    time.sleep(5)  # Wait for 2 seconds before checking again

            elif response_data['status'] == 'NotStarted':
                print("Validation request has not started. Waiting...")
            elif response_data['status'] == 'Running':
                print("Validation request is in progress. Waiting...")
            elif response_data['status'] == 'Unassigned':
                print("Validation request is unassigned. Waiting...")
            else:
                print("Validation request failed...")
                return None