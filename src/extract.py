import os
import json
import time
import requests
from config import CACHE_DIR, CACHE_FILE


class Extract:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token
        self.document_cache = None

    def _ensure_cache_directory(self):
        """Ensure the cache directory exists."""
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

    def _load_cache_if_needed(self):
        """Load cache only when it's needed."""
        if self.document_cache is None:
            self.document_cache = self._load_cache_from_file()

    def _load_cache_from_file(self):
        """Load the cache from a JSON file or return an empty dict if it doesn't exist."""
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as cache_file:
                return json.load(cache_file)
        return {}

    def _save_cache_to_file(self):
        """Save the cache to a JSON file."""
        self._ensure_cache_directory()
        with open(CACHE_FILE, "w") as cache_file:
            json.dump(self.document_cache, cache_file, indent=4)

    def _update_document_stage(
        self,
        document_id: str,
        new_stage: str,
        operation_id: str,
    ) -> None:
        self._load_cache_if_needed()
        """Update the document stage in the cache."""
        if document_id in self.document_cache:
            self.document_cache[document_id]["stage"] = new_stage
            self.document_cache[document_id]["extract_operation_id"] = operation_id
            self._save_cache_to_file()

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
            # Make the POST request
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
                        print("Document Extraction Complete!\n")
                        self._update_document_stage(
                            document_id, "extracted", operation_id
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
