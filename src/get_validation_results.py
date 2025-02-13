import os
import sqlite3
from dotenv import load_dotenv
from utils.auth import initialize_authentication
from utils.write_results import WriteResults
from modules.async_request_handler import submit_validation_request


# Cache configuration
CACHE_DIR = "cache"
SQLITE_DB_PATH = os.path.join(CACHE_DIR, "document_cache.db")

# Load environment variables and initialize authentication
load_dotenv()
base_url = os.getenv("BASE_URL")

auth = initialize_authentication()
bearer_token = auth.bearer_token


def get_extraction_validation_submitted_ids():
    """Fetches all validation_extraction_operation_id for records with stage 'extraction-validation-submitted'."""
    connection = sqlite3.connect(SQLITE_DB_PATH)
    cursor = connection.cursor()
    query = "SELECT filename, document_id, extraction_validation_operation_id, project_id, extractor_id FROM documents WHERE stage = 'extraction-validation-submitted'"
    cursor.execute(query)
    results = cursor.fetchall()
    connection.close()
    return results


def process_validation_requests():
    """Submits validation requests for each operation ID with the appropriate project and extractor IDs."""
    extraction_ids = get_extraction_validation_submitted_ids()

    for (
        filename,
        document_id,
        extraction_validation_operation_id,
        project_id,
        extractor_id,
    ) in extraction_ids:
        if extraction_validation_operation_id:
            validation_results = submit_validation_request(
                action="extraction_validation",
                bearer_token=bearer_token,
                base_url=base_url,
                project_id=project_id,
                operation_id=extraction_validation_operation_id,
                module_id=extractor_id,
            )

            # Check if validation result indicates completion
            if (
                isinstance(validation_results, dict)
                and validation_results.get("result", {})
                .get("actionData", {})
                .get("status")
                == "Completed"
            ):
                print(
                    f"Validation Result for Document ID {document_id} has been completed."
                )

                write_validated_results(
                    validated_results=validation_results,
                    extraction_results=None,
                    document_path=filename,
                )
            else:
                print(
                    f"Validation not completed for Document ID {document_id}. Status: {validation_results}"
                )
        else:
            print(f"No operation_id found for Document ID {document_id}")


def write_validated_results(validated_results, extraction_results, document_path):
    write_results = WriteResults(
        document_path=document_path,
        extraction_results=extraction_results,
        validation_extraction_results=validated_results,
    )
    write_results.write_results()


if __name__ == "__main__":
    process_validation_requests()
