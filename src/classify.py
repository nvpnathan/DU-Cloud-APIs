import time
import sqlite3
import requests
from config import SQLITE_DB_PATH


class Classify:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def _get_document_from_db(self, document_id):
        """Retrieve the document data from the database by document_id."""
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM documents WHERE document_id = ?
        """,
            (document_id,),
        )
        result = cursor.fetchone()
        conn.close()
        return result

    def _update_document_stage(
        self,
        document_id: str,
        document_type_id: str,
        classification_duration: float,
        new_stage: str,
        operation_id: str,
    ) -> None:
        """Update the document stage in the SQLite database."""
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Update document data in the database
        cursor.execute(
            """
            UPDATE documents
            SET stage = ?, document_type_id = ?, classify_operation_id = ?,
            classification_duration = ?, timestamp = ?
            WHERE document_id = ?
        """,
            (
                new_stage,
                document_type_id,
                operation_id,
                classification_duration,
                time.time(),
                document_id,
            ),
        )

        conn.commit()
        conn.close()

    def _parse_classification_results(
        self,
        classification_results: dict,
        filename: str,
        classification_duration: float,
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
            for result in classification_results["result"]["classificationResults"]:
                document_id = result["DocumentId"]
                document_type_id = result["DocumentTypeId"]
                classification_confidence = result["Confidence"]
                start_page = result["DocumentBounds"]["StartPage"]
                page_count = result["DocumentBounds"]["PageCount"]
                classifier_name = result["ClassifierName"]

                # Insert the classification results into the SQLite database
                self._insert_classification_results(
                    document_id,
                    filename,
                    document_type_id,
                    classification_confidence,
                    start_page,
                    page_count,
                    classifier_name,
                    operation_id,
                )
                self._update_document_stage(
                    document_id,
                    document_type_id,
                    classification_duration,
                    new_stage="classified",
                    operation_id=operation_id,
                )
        except ValueError as ve:
            print(f"Error parsing JSON response: {ve}")
            return None

    def _insert_classification_results(
        self,
        document_id: str,
        filename: str,
        document_type_id: str,
        classification_confidence: float,
        start_page: int,
        page_count: int,
        classifier_name: str,
        operation_id: str,
    ) -> None:
        """Insert classification results into the SQLite database."""
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Insert classification results into the 'classifications' table
        cursor.execute(
            """
            INSERT INTO classifications (document_id, filename, document_type_id, classification_confidence,
                                         start_page, page_count, classifier_name, operation_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                document_id,
                filename,
                document_type_id,
                classification_confidence,
                start_page,
                page_count,
                classifier_name,
                operation_id,
            ),
        )

        conn.commit()
        conn.close()

    def classify_document(
        self,
        document_path: str,
        document_id: str,
        classifier: str,
        classification_prompts: dict,
        validate_classification: bool = False,
    ) -> dict | None:
        # Update the cache to indicate the classification process has started
        self._update_document_stage(
            document_id,
            document_type_id=None,
            classification_duration=None,
            new_stage="classify_init",
            operation_id=None,
        )
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
            classification_start_time = time.time()
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

                    classification_end_time = time.time()
                    classification_duration = (
                        classification_end_time - classification_start_time
                    )
                    self._parse_classification_results(
                        classification_results,
                        document_path,
                        classification_duration,
                        operation_id,
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
