import time
import sqlite3
import requests
from config import SQLITE_DB_PATH
from api_utils import submit_async_request


class Classify:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def _update_document_stage(
        self,
        document_id: str,
        document_type_id: str,
        classification_duration: float,
        operation_id: str,
        new_stage: str,
    ) -> None:
        """Update the document stage in the SQLite database."""
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Update document data in the database
        cursor.execute(
            """
            UPDATE documents
            SET stage = ?, document_type_id = ?, classification_operation_id = ?,
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
            INSERT INTO classification (document_id, filename, document_type_id, classification_confidence,
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
            operation_id=None,
            new_stage="classify_init",
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
                        module_url=f"classifiers/{classifier}/classification",
                        operation_id=operation_id,
                        document_id=document_id,
                        bearer_token=self.bearer_token,
                    )

                    if validate_classification:
                        return classification_results

                    self._parse_classification_results(
                        classification_results, document_path, operation_id
                    )

                    document_type_id = classification_results["classificationResults"][
                        0
                    ]["DocumentTypeId"]
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
