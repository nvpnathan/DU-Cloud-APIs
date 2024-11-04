import time
import sqlite3
import requests
from config import SQLITE_DB_PATH


class Extract:
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
        extract_duration: float,
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
            SET stage = ?, extract_operation_id = ?, extract_duration = ?, timestamp = ?
            WHERE document_id = ?
        """,
            (new_stage, operation_id, extract_duration, time.time(), document_id),
        )

        conn.commit()
        conn.close()

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
            extract_start_time = time.time()
            response = requests.post(api_url, json=data, headers=headers, timeout=300)
            response.raise_for_status()  # Raise an exception for HTTP errors

            if response.status_code == 202:
                print("Document submitted for extraction!\n")
                response_data = response.json()
                # Extract and return operationId
                operation_id = response_data.get("operationId")

                # Wait until extraction request is completed
                if operation_id:
                    extraction_results = self.submit_extraction_request(
                        extractor_id, operation_id
                    )
                    if extraction_results:
                        extract_end_time = time.time()
                        extract_duration = extract_end_time - extract_start_time
                        print("Document Extraction Complete!\n")
                        self._update_document_stage(
                            document_id, extract_duration, "extracted", operation_id
                        )
                    return extraction_results

            print(f"Error: {response.status_code} - {response.text}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error submitting extraction request: {e}")
            # Handle network-related errors
        except Exception as ex:
            print(f"An error occurred during extraction: {ex}")
            # Handle any other unexpected errors

    def submit_extraction_request(self, extractor_id, operation_id):
        # Define the API endpoint for validation
        api_url = f"{self.base_url}{self.project_id}/extractors/{extractor_id}/extraction/result/{operation_id}?api-version=1.0"

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
                    return response_data["result"]
                elif response_data["status"] == "NotStarted":
                    print("Document Extraction not started...")
                elif response_data["status"] == "Running":
                    time.sleep(1)
                    print("Document Extraction running...")
                else:
                    print(f"Document Extraction failed. OperationID: {operation_id}")
                    print(response_data)
                    # Handle the failure condition as required
                    break

        except requests.exceptions.RequestException as e:
            print(f"Error submitting extraction request: {e}")
            # Handle network-related errors
        except KeyError as ke:
            print(f"KeyError: {ke}")
            # Handle missing keys in the response JSON
        except Exception as ex:
            print(f"An error occurred during extraction: {ex}")
            # Handle any other unexpected errors
            return None
