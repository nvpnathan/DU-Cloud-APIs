import time
import requests
from result_utils import CSVWriter

csv_writer = CSVWriter()


class Classify:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def _parse_classification_results(
        self, classification_results: dict, filename: str
    ):
        try:
            document_type_id = None
            classification_confidence = None
            start_page = None
            page_count = None
            classifier_name = None

            # Parse classification results to find the document type, confidence, start_page, and page_count
            for result in classification_results["result"]["classificationResults"]:
                document_type_id = result["DocumentTypeId"]
                classification_confidence = result["Confidence"]
                start_page = result["DocumentBounds"]["StartPage"]
                page_count = result["DocumentBounds"]["PageCount"]
                classifier_name = result["ClassifierName"]

                # Write the classification results to CSV using CSVWriter
                csv_writer.write_classification_results(
                    filename,
                    document_type_id,
                    classification_confidence,
                    start_page,
                    page_count,
                    classifier_name,
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
        # Define the API endpoint for document classification
        api_url = f"{self.base_url}{self.project_id}/classifiers/{classifier}/classification/start?api-version=1"

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
                    classification_results = self.submit_classification_request(
                        classifier, operation_id
                    )

                    if validate_classification:
                        return classification_results["result"]

                    self._parse_classification_results(
                        classification_results,
                        document_path,
                    )

                    document_type_id = classification_results["result"][
                        "classificationResults"
                    ][0]["DocumentTypeId"]
                    print(f"Classification: {document_type_id}\n")

                    return document_type_id

            print(f"Error: {response.status_code} - {response.text}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error submitting classification request: {e}")
            # Handle network-related errors
        except Exception as ex:
            print(f"An error occurred during classification: {ex}")
            # Handle any other unexpected errors

    def submit_classification_request(self, classifier, operation_id):
        # Define the API endpoint for validation
        api_url = f"{self.base_url}{self.project_id}/classifiers/{classifier}/classification/result/{operation_id}?api-version=1.0"

        # Define the headers with the Bearer token and content type
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.bearer_token}",
        }

        try:
            while True:
                response = requests.get(api_url, headers=headers, timeout=60)
                response.raise_for_status()  # Raise an exception for HTTP errors

                response_data = response.json()

                if response_data["status"] == "Succeeded":
                    classification_results = response_data
                    return classification_results

                elif response_data["status"] == "NotStarted":
                    print("Document Classification not started...")
                elif response_data["status"] == "Running":
                    time.sleep(1)
                    print("Document Classification running...")
                else:
                    print(
                        f"Document Classification failed. OperationID: {operation_id}"
                    )
                    print(response_data)
                    # Handle the failure condition as required
                    break

        except requests.exceptions.RequestException as e:
            print(f"Error submitting classification request: {e}")
            # Handle network-related errors
        except KeyError as ke:
            print(f"KeyError: {ke}")
            # Handle missing keys in the response JSON
        except Exception as ex:
            print(f"An error occurred during classification: {ex}")
            # Handle any other unexpected errors
            return None
