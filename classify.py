import requests

class Classify:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def classify_document(self, document_id):
        # Define the API endpoint for document classification
        api_url = f"{self.base_url}{self.project_id}/classifiers/ml-classification/classification?api-version=1"

        # Define the headers with the Bearer token and content type
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
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
                    classification_results = response.json()
                    document_type_id = None
                    classification_confidence = None
                    for result in classification_results['classificationResults']:
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
