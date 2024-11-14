import requests
from api_utils import submit_async_request


class Extract:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def extract_document(
        self, extractor_id: str, document_id: str, prompts: dict = None
    ) -> dict | None:
        # Define the API endpoint for document extraction
        api_url = f"{self.base_url}{self.project_id}/extractors/{extractor_id}/extraction/start?api-version=1"

        # Define the headers with the Bearer token and content type
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "text/plain",
            "Content-Type": "application/json",
        }

        data = {"documentId": f"{document_id}", **(prompts or {})}

        try:
            response = requests.post(api_url, json=data, headers=headers, timeout=300)
            response.raise_for_status()  # Raise an exception for HTTP errors

            if response.status_code == 202:
                print("Document submitted for extraction!\n")
                response_data = response.json()
                # Extract and return operationId
                operation_id = response_data.get("operationId")

                # Wait until extraction request is completed
                if operation_id:
                    extraction_results = submit_async_request(
                        action="extraction",
                        base_url=self.base_url,
                        project_id=self.project_id,
                        module_url=f"extractors/{extractor_id}/extraction",
                        operation_id=operation_id,
                        document_id=document_id,
                        bearer_token=self.bearer_token,
                    )
                    if extraction_results:
                        print("Document Extraction Complete!\n")
                    return extraction_results

            print(f"Error: {response.status_code} - {response.text}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error submitting extraction request: {e}")
            # Handle network-related errors
        except Exception as ex:
            print(f"An error occurred during extraction: {ex}")
            # Handle any other unexpected errors
