import os
import time
import sqlite3
import requests
import mimetypes
from datetime import datetime, timedelta
from api_utils import submit_async_request
from config import CACHE_EXPIRY_DAYS, SQLITE_DB_PATH
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Digitize:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token
        self.action = "digitization"

    def _execute_sql(self, query, params=()):
        """Helper method to execute an SQL query."""
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def _get_document_id_from_cache(self, filename: str) -> str | None:
        """Retrieve the document_id based on the filename and validate its timestamp."""
        result = self._execute_sql(
            "SELECT document_id, timestamp FROM documents WHERE filename = ?",
            (filename,),
        )
        if result:
            document_id, timestamp = result[0]
            cache_time = datetime.fromtimestamp(timestamp)
            if datetime.now() - cache_time > timedelta(days=CACHE_EXPIRY_DAYS):
                logging.info(f"Cache expired for document: {filename}")
                self._remove_document_from_cache(filename)
                return None
            return document_id
        return None

    def _update_cache(
        self,
        filename: str,
        document_id: str | None,
        stage: str,
        error_code=None,
        error_message=None,
    ):
        """Insert or update the document cache."""
        # Update the row if it exists
        self._execute_sql(
            """
            UPDATE documents
            SET document_id = ?, stage = ?, timestamp = ?, error_code = ?, error_message = ?
            WHERE filename = ?
            """,
            (document_id, stage, time.time(), error_code, error_message, filename),
        )

        # If no row was updated, insert a new one
        self._execute_sql(
            """
            INSERT INTO documents (document_id, filename, stage, timestamp, error_code, error_message)
            SELECT ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM documents WHERE filename = ?
            )
            """,
            (
                document_id,
                filename,
                stage,
                time.time(),
                error_code,
                error_message,
                filename,
            ),
        )

    def _remove_document_from_cache(self, filename: str) -> None:
        """Remove a document from the cache based on its filename."""
        self._execute_sql("DELETE FROM documents WHERE filename = ?", (filename,))

    def _log_error(self, filename, action, error_code, error_message):
        """Log an error and update the database."""
        logging.error(
            f"{action.capitalize()} failed for {filename}. Code: {error_code}, Message: {error_message}"
        )
        self._update_cache(
            filename, None, f"{action}_failed", error_code, error_message
        )

    def _prepare_file(self, document_path: str):
        """Prepare the file for upload."""
        mime_type, _ = mimetypes.guess_type(document_path)
        mime_type = mime_type or "multipart/form-data"
        return {
            "File": (
                os.path.basename(document_path),
                open(document_path, "rb"),
                mime_type,
            )
        }

    def digitize(self, document_path: str) -> str | None:
        """Digitize a document and handle caching."""
        filename = os.path.basename(document_path)
        cached_document_id = self._get_document_id_from_cache(filename)
        if cached_document_id:
            logging.info(
                f"Using cached document ID: {cached_document_id} for {filename}"
            )
            return cached_document_id

        # Log the initiation stage with no document_id
        self._update_cache(filename, None, "init")

        api_url = f"{self.base_url}{self.project_id}/digitization/start?api-version=1"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "text/plain",
        }

        try:
            files = self._prepare_file(document_path)
            response = requests.post(api_url, files=files, headers=headers, timeout=60)
            response.raise_for_status()

            if response.status_code == 202:
                response_data = response.json()
                document_id = response_data.get("documentId")
                if not document_id:
                    raise ValueError("Missing documentId in the response.")

                # Update cache with the retrieved document_id
                self._update_cache(filename, document_id, "digitize-pending")

                digitize_results = submit_async_request(
                    action=self.action,
                    base_url=self.base_url,
                    project_id=self.project_id,
                    module_id="digitization",
                    operation_id=document_id,
                    document_id=document_id,
                    bearer_token=self.bearer_token,
                )

                if digitize_results:
                    return digitize_results.get("documentObjectModel", {}).get(
                        "documentId"
                    )

            self._log_error(
                filename, self.action, str(response.status_code), response.text
            )
        except requests.exceptions.RequestException as e:
            self._log_error(filename, self.action, "NetworkError", str(e))
        except Exception as ex:
            self._log_error(filename, self.action, "UnexpectedError", str(ex))
        return None
