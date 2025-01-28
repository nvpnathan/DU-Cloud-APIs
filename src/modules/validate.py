import sqlite3
import requests
from project_config import SQLITE_DB_PATH
from .async_request_handler import submit_validation_request


class Validate:
    def __init__(self, base_url, project_id, bearer_token):
        self.base_url = base_url
        self.project_id = project_id
        self.bearer_token = bearer_token

    def _update_document_stage(
        self,
        action: str,
        document_id: str,
        new_stage: str,
        operation_id: str,
        error_code: str,
        error_message: str,
    ) -> None:
        """Update the document stage in the SQLite database."""
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            cursor = conn.cursor()

            # Define the column names dynamically based on the action
            operation_id_column = f"{action}_operation_id"

            cursor.execute(
                f"""
                UPDATE documents
                SET stage = ?, {operation_id_column} = ?, error_code = ?, error_message = ?
                WHERE document_id = ?
                """,
                (
                    new_stage,
                    operation_id,
                    error_code,
                    error_message,
                    document_id,
                ),
            )

            conn.commit()

    def validate_extraction_results(
        self,
        extractor_id: str,
        document_id: str,
        extraction_results: dict,
        extraction_prompts: dict,
    ) -> dict | None:
        # Define the API endpoint for validation
        api_url = f"{self.base_url}{self.project_id}/extractors/{extractor_id}/validation/start?api-version=1.1"

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
                    self._update_document_stage(
                        action="extraction_validation",
                        document_id=document_id,
                        new_stage="extraction-validation-submitted",
                        operation_id=operation_id,
                        error_code=None,
                        error_message=None,
                    )

                    validation_result = submit_validation_request(
                        action="extraction_validation",
                        bearer_token=self.bearer_token,
                        base_url=self.base_url,
                        project_id=self.project_id,
                        operation_id=operation_id,
                        module_id=extractor_id,
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

    def validate_classification_results(
        self,
        document_id: str,
        classifier_id: str,
        classification_results: dict,
        classificastion_prompts: dict,
    ) -> str | None:
        # Define the API endpoint for validation
        api_url = f"{self.base_url}{self.project_id}/classifiers/{classifier_id}/validation/start?api-version=1.1"

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
                    self._update_document_stage(
                        action="classification_validation",
                        document_id=document_id,
                        new_stage="classification-validation-submitted",
                        operation_id=operation_id,
                        error_code=None,
                        error_message=None,
                    )
                    validation_result = submit_validation_request(
                        action="classification_validation",
                        bearer_token=self.bearer_token,
                        base_url=self.base_url,
                        project_id=self.project_id,
                        operation_id=operation_id,
                        module_id=classifier_id,
                    )
                    print("Classification Validation Complete!\n")

                    if validation_result:
                        document_type_id = validation_result["result"][
                            "validatedClassificationResults"
                        ][0]["DocumentTypeId"]
                        return document_type_id

            print(f"Error: {response.status_code} - {response.text}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error submitting classification validation request: {e}")
            # Handle network-related errors
        except Exception as ex:
            print(f"An error occurred during classification validation: {ex}")
            # Handle any other unexpected errors
