from project_setup import initialize_environment
from processor import DocumentProcessor

if __name__ == "__main__":
    # Initialize environment (clients, config, context)
    config, context, clients = initialize_environment()

    # Unpack the clients tuple into individual components
    digitize_client, classify_client, extract_client, validate_client = clients

    # Define the document folder
    DOCUMENT_FOLDER = "example_documents"

    # Create and run the processor
    processor = DocumentProcessor(
        digitize_client=digitize_client,
        classify_client=classify_client,
        extract_client=extract_client,
        validate_client=validate_client,
    )

    # Process documents in the folder
    processor.process_documents_in_folder(DOCUMENT_FOLDER, config, context)
