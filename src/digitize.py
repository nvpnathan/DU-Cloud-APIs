import os
import json
import time
import requests
import mimetypes
from datetime import datetime, timedelta

CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "document_cache.json")
CACHE_EXPIRY_DAYS = 7  # Cache expiry in days


class Digitize:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token
        self.document_cache = self._load_cache_from_file()

    def _ensure_cache_directory(self):
        """Ensure the cache directory exists."""
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

    def _save_cache_to_file(self):
        """Save the cache to a JSON file."""
        self._ensure_cache_directory()
        with open(CACHE_FILE, "w") as cache_file:
            json.dump(self.document_cache, cache_file)

    def _load_cache_from_file(self):
        """Load the cache from a JSON file or return an empty dict if it doesn't exist."""
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as cache_file:
                return json.load(cache_file)
        return {}

    def _get_document_id_from_cache(self, document_path: str) -> str | None:
        """Check if the document_id is in the cache and validate its timestamp."""
        cache_entry = self.document_cache.get(document_path)

        if cache_entry:
            document_id = cache_entry.get("document_id")
            timestamp = cache_entry.get("timestamp")

            # Check if the entry is older than 7 days
            cache_time = datetime.fromtimestamp(timestamp)
            if datetime.now() - cache_time > timedelta(days=CACHE_EXPIRY_DAYS):
                print(f"Cache expired for document: {document_path}")
                # Remove the expired entry from cache
                self.document_cache.pop(document_path)
                self._save_cache_to_file()
                return None
            else:
                return document_id
        return None

    def _add_document_to_cache(self, document_path: str, document_id: str) -> None:
        """Add a document to the cache with its document_id and a timestamp."""
        self.document_cache[document_path] = {
            "document_id": document_id,
            "timestamp": time.time(),
        }
        self._save_cache_to_file()

    def digitize(self, document_path: str) -> str | None:
        """Digitize a document and handle caching."""
        # Check if the document_id is already in the cache
        cached_document_id = self._get_document_id_from_cache(document_path)
        if cached_document_id:
            print(f"Using cached document ID: {cached_document_id} for {document_path}")
            return cached_document_id

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
                        # Add the digitized document to the cache
                        self._add_document_to_cache(document_path, digitize_results)
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
