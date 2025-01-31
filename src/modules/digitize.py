import os
import logging
import requests
import mimetypes
from .async_request_handler import submit_async_request
from utils.db_utils import get_document_id_from_cache, update_cache

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

    def _log_error(self, filename, action, error_code, error_message):
        """Log an error and update the database."""
        logging.error(
            f"{action.capitalize()} failed for {filename}. Code: {error_code}, Message: {error_message}"
        )
        update_cache(filename, None, f"{action}_failed", error_code, error_message)

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
        cached_document_id = get_document_id_from_cache(filename)
        if cached_document_id:
            logging.info(
                f"Using cached document ID: {cached_document_id} for {filename}"
            )
            return cached_document_id

        # Log the initiation stage with no document_id
        update_cache(
            filename=filename,
            document_id=None,
            stage="init",
            project_id=self.project_id,
        )

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
                update_cache(
                    filename=filename,
                    document_id=document_id,
                    stage="digitize-pending",
                    project_id=self.project_id,
                )

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
