import os
import time
import sqlite3
import requests
import mimetypes
from datetime import datetime, timedelta
from api_utils import submit_async_request
from config import CACHE_EXPIRY_DAYS, SQLITE_DB_PATH


class Digitize:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

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
        self,
        filename: str,
        stage: str,
        document_id: str,
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
            INSERT OR REPLACE INTO documents (document_id, filename, stage, timestamp)
            VALUES (?, ?, ?, ?)
        """,
            (
                document_id,
                filename,
                stage,
                time.time(),
            ),
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
            self._update_cache_with_document_id(
                filename, document_id="pending", stage="init"
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

            response = requests.post(api_url, files=files, headers=headers, timeout=60)
            response.raise_for_status()

            if response.status_code == 202:
                print("Document successfully digitized!")
                response_data = response.json()
                document_id = response_data.get("documentId")
                self._update_cache_with_document_id(
                    filename, document_id=document_id, stage="digitize-pending"
                )
                # Wait for digitization completion
                if document_id:
                    digitize_results = submit_async_request(
                        action="digitization",
                        base_url=self.base_url,
                        project_id=self.project_id,
                        module_url="digitization",
                        operation_id=document_id,
                        document_id=document_id,
                        bearer_token=self.bearer_token,
                    )
                    if digitize_results:
                        document_id = digitize_results.get(
                            "documentObjectModel", {}
                        ).get("documentId")
                        return document_id

            print(f"Error: {response.status_code} - {response.text}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error submitting digitization request: {e}")
            return None
        except Exception as ex:
            print(f"An error occurred during digitization: {ex}")
            return None
