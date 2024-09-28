import time
import requests


class Validate:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def validate_extraction_results(
        self,
        extractor_id: str,
        document_id: str,
        extraction_results: dict,
        extraction_prompts: dict,
    ) -> dict | None:
        # Define the API endpoint for validation
        api_url = f"{self.base_url}{self.project_id}/extractors/{extractor_id}/validation/start?api-version=1"

        # Define the headers with the Bearer token and content type
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "text/plain",
            "Content-Type": "application/json",
        }

        data = {
            "documentId": document_id,
            "actionTitle": f"Validate - {extractor_id}",
            "actionPriority": "Medium",
            "actionCatalog": "default_du_actions",
            "actionFolder": "Shared",
            "storageBucketName": "du_storage_bucket",
            "storageBucketDirectoryPath": "du_storage_bucket",
            **extraction_results,
            **(extraction_prompts or {}),
        }

        try:
            # Make the POST request to initiate validation
            response = requests.post(api_url, json=data, headers=headers, timeout=60)
            response.raise_for_status()  # Raise an exception for HTTP errors

            if response.status_code == 202:
                print("\nExtraction Validation request sent!")
                # Parse the JSON response
                response_data = response.json()
                # Extract and return the operationId
                operation_id = response_data.get("operationId")

                # Wait until the validation operation is completed
                if operation_id:
                    validation_result = self.submit_extraction_validation_request(
                        extractor_id, operation_id
                    )
                print("Extraction Validation Complete!\n")
                return validation_result
            print(f"Error: {response.status_code} - {response.text}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error submitting extraction validation request: {e}")
            # Handle network-related errors
        except Exception as ex:
            print(f"An error occurred during extraction validation: {ex}")
            # Handle any other unexpected errors

    def submit_extraction_validation_request(
        self, extractor_id: str, operation_id: str
    ):
        # Define the API endpoint for validation
        api_url = f"{self.base_url}{self.project_id}/extractors/{extractor_id}/validation/result/{operation_id}?api-version=1"

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
                    print("Extraction Validation request submitted successfully!")
                    while True:
                        response = requests.get(api_url, headers=headers, timeout=60)
                        response_data = response.json()
                        # Check the status inside actionData
                        action_data_status = response_data["result"]["actionData"][
                            "status"
                        ]
                        print(
                            f"Validate Document Extraction action status: {action_data_status}"
                        )
                        if action_data_status == "Unassigned":
                            print(
                                "Validation Document Extraction is unassigned. Waiting..."
                            )
                        elif action_data_status == "Pending":
                            print(
                                "Validate Document Extraction in progress. Waiting..."
                            )
                        elif action_data_status == "Completed":
                            print("Validate Document Extraction is completed.")
                            return response_data
                        else:
                            print("Unknown validation action status.")
                        time.sleep(5)  # Wait for 5 seconds before checking again

                elif response_data["status"] == "NotStarted":
                    print("Extraction Validation request has not started. Waiting...")
                elif response_data["status"] == "Running":
                    print("Extraction Validation request is in progress. Waiting...")
                elif response_data["status"] == "Unassigned":
                    print("Extraction Validation request is unassigned. Waiting...")
                else:
                    print("Extraction Validation request failed...")
                    return None
        except requests.exceptions.RequestException as e:
            print(f"Error submitting extraction validation request: {e}")
            # Handle network-related errors
        except KeyError as ke:
            print(f"KeyError: {ke}")
            # Handle missing keys in the response JSON
        except Exception as ex:
            print(f"An error occurred during extraction validation: {ex}")
            # Handle any other unexpected errors
            return None

    def validate_classification_results(
        self,
        document_id: str,
        classifier_id: str,
        classification_results: dict,
        classificastion_prompts: dict,
    ) -> str | None:
        # Define the API endpoint for validation
        api_url = f"{self.base_url}{self.project_id}/classifiers/{classifier_id}/validation/start?api-version=1"

        document_type_id = classification_results["classificationResults"][0][
            "DocumentTypeId"
        ]
        # Define the headers with the Bearer token and content type
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "text/plain",
            "Content-Type": "application/json",
        }

        # Define the payload data
        data = {
            "documentId": document_id,
            "actionTitle": f"Validate - {document_type_id}",
            "actionPriority": "Medium",
            "actionCatalog": "default_du_actions",
            "actionFolder": "Shared",
            "storageBucketName": "du_storage_bucket",
            "storageBucketDirectoryPath": "du_storage_bucket",
            **classification_results,
            **(classificastion_prompts or {}),
        }

        try:
            # Make the POST request to initiate validation
            response = requests.post(api_url, json=data, headers=headers, timeout=60)
            response.raise_for_status()  # Raise an exception for HTTP errors

            if response.status_code == 202:
                print("\nClassification Validation request sent!")
                # Parse the JSON response
                response_data = response.json()
                # Extract and return the operationId
                operation_id = response_data.get("operationId")

                # Wait until the validation operation is completed
                if operation_id:
                    validation_result = self.submit_classification_validation_request(
                        operation_id
                    )
                print("Classification Validation Complete!\n")

                if validation_result:
                    document_type_id = validation_result["result"][
                        "validatedClassificationResults"
                    ][0]["DocumentTypeId"]
                    return document_type_id
                print("Validation result is None.")
                return None
            print(f"Error: {response.status_code} - {response.text}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error submitting classification validation request: {e}")
            # Handle network-related errors
        except Exception as ex:
            print(f"An error occurred during classification validation: {ex}")
            # Handle any other unexpected errors

    def submit_classification_validation_request(
        self, operation_id: str
    ) -> dict | None:
        api_url = f"{self.base_url}{self.project_id}/classifiers/ml-classification/validation/result/{operation_id}?api-version=1"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.bearer_token}",
        }
        try:
            while True:
                response = requests.get(api_url, headers=headers, timeout=60)
                response_data = response.json()
                if response_data["status"] == "Succeeded":
                    print("Classification Validation request submitted successfully!")
                    while True:
                        response = requests.get(api_url, headers=headers, timeout=60)
                        response_data = response.json()
                        # Check the status inside actionData
                        action_data_status = response_data["result"]["actionData"][
                            "status"
                        ]
                        print(
                            f"Validate Document Classification action status: {action_data_status}"
                        )
                        if action_data_status == "Unassigned":
                            print(
                                "Validation Document Classification is unassigned. Waiting..."
                            )
                        elif action_data_status == "Pending":
                            print(
                                "Validate Document Classification in progress. Waiting..."
                            )
                        elif action_data_status == "Completed":
                            print("Validate Document Classification is completed.")
                            return response_data
                        else:
                            print("Unknown validation action status.")
                        time.sleep(5)  # Wait for 5 seconds before checking again

                elif response_data["status"] == "NotStarted":
                    print(
                        "Classification Validation request has not started. Waiting..."
                    )
                elif response_data["status"] == "Running":
                    print(
                        "Classification Validation request is in progress. Waiting..."
                    )
                elif response_data["status"] == "Unassigned":
                    print("Classification Validation request is unassigned. Waiting...")
                else:
                    print("Classification Validation request failed...")
                    return None
        except requests.exceptions.RequestException as e:
            print(f"Error submitting extraction validation request: {e}")
            # Handle network-related errors
        except KeyError as ke:
            print(f"KeyError: {ke}")
            # Handle missing keys in the response JSON
        except Exception as ex:
            print(f"An error occurred during extraction validation: {ex}")
            # Handle any other unexpected errors
            return None
