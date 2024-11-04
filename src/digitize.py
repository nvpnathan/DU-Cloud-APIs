import os
import time
import sqlite3
import requests
import mimetypes
from datetime import datetime, timedelta
from config import CACHE_EXPIRY_DAYS, SQLITE_DB_PATH


class Digitize:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def _add_document_to_cache(
        self, filename: str, digitize_duration: str, stage: str, document_id: str
    ) -> None:
        """Add a document to the cache in the SQLite database."""
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO documents (document_id, filename, digitize_duration, stage, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """,
            (document_id, filename, digitize_duration, stage, time.time()),
        )
        conn.commit()
        conn.close()

    def _get_document_id_from_cache(self, filename: str) -> str | None:
        """Retrieve the document_id based on the filename and validate its timestamp."""
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT document_id, timestamp FROM documents WHERE filename = ?
        """,
            (filename,),
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            document_id, timestamp = result
            cache_time = datetime.fromtimestamp(timestamp)
            if datetime.now() - cache_time > timedelta(days=CACHE_EXPIRY_DAYS):
                print(f"Cache expired for document: {filename}")
                self._remove_document_from_cache(document_id)
                return None
            return document_id
        return None

    def _update_cache_with_document_id(
        self, filename: str, digitize_duration: str, stage: str, new_document_id: str
    ) -> None:
        """Update the cache by replacing 'pending' with the actual document_id."""
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Delete pending entry if it exists
        cursor.execute(
            """
            DELETE FROM documents WHERE document_id = "pending" AND filename = ?
        """,
            (filename,),
        )

        # Insert or update the actual document_id entry
        cursor.execute(
            """
            INSERT OR REPLACE INTO documents (document_id, filename, digitize_duration, stage, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """,
            (new_document_id, filename, digitize_duration, stage, time.time()),
        )
        conn.commit()
        conn.close()

    def _remove_document_from_cache(self, document_id: str) -> None:
        """Remove a document from the cache based on its document_id."""
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
        conn.commit()
        conn.close()

    def digitize(self, document_path: str) -> str | None:
        """Digitize a document and handle caching."""
        # Get the filename from the document path
        filename = os.path.basename(document_path)

        # Check if the document_id is already cached using the filename
        cached_document_id = self._get_document_id_from_cache(filename)
        if cached_document_id:
            print(f"Using cached document ID: {cached_document_id} for {filename}")
            return cached_document_id
        else:
            # Since we don't have the document_id yet, temporarily add the document with None
            self._add_document_to_cache(
                filename, digitize_duration=None, stage="init", document_id="pending"
            )

        # Define the API endpoint for digitization
        api_url = f"{self.base_url}{self.project_id}/digitization/start?api-version=1"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "text/plain",
        }

        try:
            # Get Document mime type
            mime_type, _ = mimetypes.guess_type(document_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

            # Open the file and prepare the request
            files = {"File": (document_path, open(document_path, "rb"), mime_type)}

            digitize_start_time = time.time()
            response = requests.post(api_url, files=files, headers=headers, timeout=300)
            response.raise_for_status()

            if response.status_code == 202:
                print("Document successfully digitized!")
                response_data = response.json()
                document_id = response_data.get("documentId")

                # Wait for digitization completion
                if document_id:
                    digitize_results = self.submit_digitization_request(document_id)
                    if digitize_results:
                        # Update the cache with the actual document_id and digitized stage
                        digitize_end_time = time.time()
                        digitize_duration = digitize_end_time - digitize_start_time
                        self._update_cache_with_document_id(
                            filename,
                            digitize_duration,
                            stage="digitized",
                            new_document_id=document_id,
                        )
                        return digitize_results

            print(f"Error: {response.status_code} - {response.text}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error submitting digitization request: {e}")
            return None
        except Exception as ex:
            print(f"An error occurred during digitization: {ex}")
            return None

    def submit_digitization_request(self, document_id: str) -> str | None:
        """Submit the digitization request and wait for completion."""
        api_url = f"{self.base_url}{self.project_id}/digitization/result/{document_id}?api-version=1"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.bearer_token}",
        }

        try:
            while True:
                response = requests.get(api_url, headers=headers, timeout=60)
                response_data = response.json()

                if response_data["status"] == "Succeeded":
                    return response_data["result"]["documentObjectModel"]["documentId"]
                elif response_data["status"] == "NotStarted":
                    print("Document Digitization not started...")
                elif response_data["status"] == "Running":
                    time.sleep(1)
                    print("Document Digitization running...")
                else:
                    print(f"Document Digitization failed. OperationID: {document_id}")
                    print(response_data)
                    break

        except requests.exceptions.RequestException as e:
            print(f"Error submitting digitization request: {e}")
        except KeyError as ke:
            print(f"KeyError: {ke}")
        except Exception as ex:
            print(f"An error occurred during digitization: {ex}")
        return None
