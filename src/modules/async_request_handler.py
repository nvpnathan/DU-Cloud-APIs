import time
import requests
from datetime import datetime
from utils.db_utils import update_document_stage


def _log_error(action, document_id, operation_id, error_code, error_message):
    print(f"{action.capitalize()} failed. OperationID: {operation_id}")
    print(f"Error Code: {error_code}, Error Message: {error_message}")
    update_document_stage(
        action=action,
        document_id=document_id,
        new_stage=f"{action}_failed",
        operation_id=operation_id,
        error_code=error_code,
        error_message=error_message,
    )


def submit_async_request(
    action: str,
    base_url: str,
    project_id: str,
    module_id: str,
    operation_id: str,
    document_id: str,
    bearer_token: str,
    max_retries: int = 15,  # Maximum retries for errors
    retry_delay: float = 2.0,  # Initial delay for retries
) -> dict:
    classifier_id = None
    extractor_id = None

    if action.startswith("digitization") and module_id:
        api_url = (
            f"{base_url}{project_id}/{module_id}/result/{operation_id}?api-version=1.1"
        )
    elif action.startswith("classification") and module_id:
        api_url = f"{base_url}{project_id}/classifiers/{module_id}/classification/result/{operation_id}?api-version=1.1"
        classifier_id = module_id
    elif action.startswith("extraction") and module_id:
        api_url = f"{base_url}{project_id}/extractors/{module_id}/extraction/result/{operation_id}?api-version=1.1"
        extractor_id = module_id
    else:
        print("Invalid action or missing Module ID for extraction.")
        return None

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {bearer_token}",
    }
    start_time = time.time()
    retries = 0

    while True:
        try:
            response = requests.get(api_url, headers=headers, timeout=60)
            response.raise_for_status()
            response_data = response.json()

            if response_data["status"] == "Succeeded":
                end_time = time.time()
                duration = end_time - start_time
                print(f"{action.capitalize()} completed successfully!")

                update_document_stage(
                    action=action,
                    document_id=document_id,
                    duration=duration,
                    new_stage=action,
                    operation_id=operation_id,
                    classifier_id=classifier_id,
                    extractor_id=extractor_id,
                )
                return response_data.get("result")

            elif response_data["status"] in {"NotStarted", "Running"}:
                print(f"{action.capitalize()} status: {response_data['status']}...")
                time.sleep(1)
                continue

            else:  # Handle failure states
                error_code = response_data.get("error", {}).get("code")
                error_message = response_data.get("error", {}).get("message")
                _log_error(action, document_id, operation_id, error_code, error_message)

                if error_code == "[IxpExtractorUnavailableError]":
                    if retries < max_retries:
                        retries += 1
                        delay = retry_delay * (
                            2 ** (retries - 1)
                        )  # Exponential backoff
                        print(
                            f"Retrying due to error: {error_code}. Retry {retries}/{max_retries} in {delay} seconds..."
                        )
                        time.sleep(delay)
                        continue  # Retry the loop
                    else:
                        raise RuntimeError(
                            f"Maximum retries reached for error {error_code}. Unable to complete the request."
                        )

                # Raise for other errors
                raise RuntimeError(
                    f"Operation {action} failed: {error_message} (Error Code: {error_code})"
                )

        except requests.exceptions.RequestException as e:
            _log_error(action, document_id, operation_id, "NetworkError", str(e))
        except KeyError as ke:
            _log_error(action, document_id, operation_id, "KeyError", str(ke))
        except Exception as ex:
            _log_error(action, document_id, operation_id, "UnexpectedError", str(ex))

        return None


def submit_validation_request(
    action: str,
    bearer_token: str,
    base_url: str,
    project_id: str,
    operation_id: str,
    module_id: str = None,
) -> dict | None:
    """
    Submits a validation request (either for classification or extraction) and waits for the process to complete.

    :param action: Type of validation ("classification" or "extraction")
    :param operation_id: Operation ID to check the result status
    :param extractor_id: Extractor ID (required for extraction validation)
    :return: The result data if successful, otherwise None
    """
    classifier_id = None
    extractor_id = None

    if action.startswith("classification"):
        api_url = f"{base_url}{project_id}/classifiers/{module_id}/validation/result/{operation_id}?api-version=1.1"
        classifier_id = module_id
    elif action.startswith("extraction") and module_id:
        api_url = f"{base_url}{project_id}/extractors/{module_id}/validation/result/{operation_id}?api-version=1.1"
        extractor_id = module_id
    else:
        print("Invalid action or missing extractor ID for extraction.")
        return None

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {bearer_token}",
    }

    try:
        while True:
            response = requests.get(api_url, headers=headers, timeout=60)
            response_data = response.json()

            if response_data.get("status") == "Succeeded":
                print(
                    f"{action.capitalize()} Validation request submitted successfully!"
                )
                while True:
                    response = requests.get(api_url, headers=headers, timeout=60)
                    response_data = response.json()

                    action_data_status = (
                        response_data.get("result", {})
                        .get("actionData", {})
                        .get("status")
                    )

                    if action_data_status is None:
                        print("Error: Missing actionData status in response.")
                        return None

                    print(
                        f"Validate Document {action.capitalize()} action status: {action_data_status}"
                    )

                    if action_data_status == "Unassigned":
                        print(
                            f"Validation Document {action.capitalize()} is unassigned. Waiting..."
                        )
                    elif action_data_status == "Pending":
                        print(
                            f"Validate Document {action.capitalize()} in progress. Waiting..."
                        )
                    elif action_data_status == "Completed":
                        print(f"Validate Document {action.capitalize()} is completed.")
                        # Extract document ID based on action type
                        document_key = (
                            "validatedExtractionResults"
                            if action == "extraction_validation"
                            else "validatedClassificationResults"
                        )
                        if action == "classification_validation":
                            document_id = response_data["result"][document_key][0][
                                "DocumentId"
                            ]
                        else:
                            document_id = response_data["result"][document_key][
                                "DocumentId"
                            ]

                        # Parse start and end times
                        start_time_str = response_data["result"]["actionData"][
                            "lastAssignedTime"  ## Not valid if directly assigned!
                        ]
                        end_time_str = response_data["result"]["actionData"][
                            "completionTime"
                        ]
                        start_time = datetime.fromisoformat(
                            start_time_str.replace("Z", "+00:00")
                        )
                        end_time = datetime.fromisoformat(
                            end_time_str.replace("Z", "+00:00")
                        )

                        # Calculate duration
                        duration = (end_time - start_time).total_seconds()
                        update_document_stage(
                            document_id=document_id,
                            action=action,
                            new_stage=action,
                            duration=duration,
                            operation_id=operation_id,
                            classifier_id=classifier_id,
                            extractor_id=extractor_id,
                        )
                        return response_data
                    else:
                        print("Unknown validation action status.")
                    time.sleep(5)  # Wait for 5 seconds before checking again

            elif response_data.get("status") == "NotStarted":
                print(
                    f"{action.capitalize()} Validation request has not started. Waiting..."
                )
            elif response_data.get("status") == "Running":
                print(
                    f"{action.capitalize()} Validation request is in progress. Waiting..."
                )
            elif response_data.get("status") == "Unassigned":
                print(
                    f"{action.capitalize()} Validation request is unassigned. Waiting..."
                )
            else:
                print(f"{action.capitalize()} Validation request failed...")
                return None

    except requests.exceptions.RequestException as e:
        print(f"Error submitting {action} validation request: {e}")
    except KeyError as ke:
        print(f"KeyError: {ke}")
        return None
    except Exception as ex:
        print(f"An error occurred during {action} validation: {ex}")
        return None
