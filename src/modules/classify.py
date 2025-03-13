import requests
from .async_request_handler import submit_async_request
from utils.db_utils import update_document_stage, insert_classification_results


class Classify:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def _parse_classification_results(
        self,
        classification_results: dict,
        filename: str,
        operation_id: str,
    ):
        try:
            # Initialize variables
            document_id = None
            document_type_id = None
            classification_confidence = None
            start_page = None
            page_count = None
            classifier_name = None

            # Parse classification results to find the document type, confidence, start_page, and page_count
            for result in classification_results["classificationResults"]:
                document_id = result["DocumentId"]
                document_type_id = result["DocumentTypeId"]
                classification_confidence = result["Confidence"]
                start_page = result["DocumentBounds"]["StartPage"]
                page_count = result["DocumentBounds"]["PageCount"]
                classifier_name = result["ClassifierName"]

                # Insert the classification results into the SQLite database
                insert_classification_results(
                    document_id,
                    filename,
                    document_type_id,
                    classification_confidence,
                    start_page,
                    page_count,
                    classifier_name,
                    operation_id,
                )
        except ValueError as ve:
            print(f"Error parsing JSON response: {ve}")
            return None

    def classify_document(
        self,
        document_path: str,
        document_id: str,
        classifier: str,
        classification_prompts: dict,
        validate_classification: bool = False,
    ) -> dict | None:
        # Update the cache to indicate the classification process has started
        update_document_stage(
            action="classification",
            document_id=document_id,
            operation_id=None,
            new_stage="classify_init",
        )
        # Define the API endpoint for document classification
        api_url = f"{self.base_url}{self.project_id}/classifiers/{classifier}/classification/start?api-version=1.1"

        # Define the headers with the Bearer token and content type
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "text/plain",
            "Content-Type": "application/json",
        }

        data = {"documentId": f"{document_id}", **(classification_prompts or {})}

        try:
            response = requests.post(api_url, json=data, headers=headers, timeout=60)
            response.raise_for_status()  # Raise an exception for HTTP errors

            if response.status_code == 202:
                print("Document submitted for classification!")
                response_data = response.json()
                # Extract and return operationId
                operation_id = response_data.get("operationId")

                # Wait until classification request is completed
                if operation_id:
                    classification_results = submit_async_request(
                        action="classification",
                        base_url=self.base_url,
                        project_id=self.project_id,
                        module_id=classifier,
                        operation_id=operation_id,
                        document_id=document_id,
                        bearer_token=self.bearer_token,
                    )

                    if validate_classification:
                        return classification_results

                    self._parse_classification_results(
                        classification_results, document_path, operation_id
                    )

                    # Extract all classified document type IDs along with their PageRanges
                    document_classifications = [
                        (
                            result["DocumentTypeId"],
                            result["DocumentBounds"]["PageRange"],
                        )
                        for result in classification_results.get(
                            "classificationResults", []
                        )
                    ]

                    print(
                        f"Classification results for {document_path}: {document_classifications}"
                    )

                    return document_classifications

            print(f"Error: {response.status_code} - {response.text}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error submitting classification request: {e}")
            # Handle network-related errors
        except Exception as ex:
            print(f"An error occurred during classification: {ex}")
            # Handle any other unexpected errors
