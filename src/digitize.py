import time
import requests
import mimetypes


class Digitize:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def digitize(self, document_path: str) -> str | None:
        # Define the API endpoint for digitization
        api_url = f"{self.base_url}{self.project_id}/digitization/start?api-version=1"

        # Define the headers with the Bearer token and content type
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "text/plain",
        }

        try:
            # Get Document mime type
            mime_type, _ = mimetypes.guess_type(document_path)
            # If the MIME type couldn't be guessed, default to 'application/octet-stream'
            if mime_type is None:
                mime_type = "application/octet-stream"

            # Open the file
            files = {"File": (document_path, open(document_path, "rb"), mime_type)}

            response = requests.post(api_url, files=files, headers=headers, timeout=60)
            response.raise_for_status()  # Raise an exception for HTTP errors

            if response.status_code == 202:
                print("Document successfully digitized!")
                response_data = response.json()
                # Extract the documentID if it exists
                document_id = response_data.get("documentId")

                # Wait until document digitization is completed
                if document_id:
                    digitize_results = self.submit_digitization_request(document_id)
                    print(f"Document ID: {document_id}\n")
                    return digitize_results

            print(f"Error: {response.status_code} - {response.text}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error submitting digitization request: {e}")
            # Handle network-related errors
            return None
        except Exception as ex:
            print(f"An error occurred during digitization: {ex}")
            # Handle any other unexpected errors
            return None

    def submit_digitization_request(self, document_id):
        # Define the API endpoint for validation
        api_url = f"{self.base_url}{self.project_id}/digitization/result/{document_id}?api-version=1"

        # Define the headers with the Bearer token and content type
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
            # Handle network-related errors
        except KeyError as ke:
            print(f"KeyError: {ke}")
            # Handle missing keys in the response JSON
            return None
        except Exception as ex:
            print(f"An error occurred during digitization: {ex}")
            # Handle any other unexpected errors
            return None
