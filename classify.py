import requests

class Classify:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def classify_document(self, document_id, validate_classification=False, classifier='ml-classification', prompts=None):
        # Define the API endpoint for document classification        
        api_url = f"{self.base_url}{self.project_id}/classifiers/{classifier}/classification?api-version=1"
        print(api_url)
        print(prompts['prompts'])
        # Define the headers with the Bearer token and content type
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "text/plain",
            "Content-Type": "application/json"
        }

        data = {
            "documentId": f"{document_id}",
            "prompts": prompts['prompts']
        }

        try:
            # Make the POST request
            response = requests.post(api_url, json=data, headers=headers)

            if response.status_code == 200:
                print("Document successfully classified!")
                # Try parsing the JSON response
                try:
                    classification_results = response.json()
                    if validate_classification:
                        return classification_results
                    else:
                        document_type_id = None
                        classification_confidence = None
                        for result in classification_results['classificationResults']:
                            if result['DocumentId'] == document_id:
                                document_type_id = result['DocumentTypeId']
                                classification_confidence = result['Confidence']
                                break
                        if document_type_id:
                            print(f"Document Type ID: {document_type_id}, Confidence: {classification_confidence}\n")
                            return document_type_id
                        else:
                            print("Document ID not found in classification results.")
                            return None
                except ValueError as ve:
                    print(f"Error parsing JSON response: {ve}")
                    return None
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"An error occurred during classification: {e}")
            return None
