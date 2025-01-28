from setup import initialize_environment
from processor import DocumentProcessor

if __name__ == "__main__":
    # Initialize environment (clients, config, context)
    config, context, clients = initialize_environment()

    # Define the document folder
    DOCUMENT_FOLDER = "example_documents"

    # Create and run the processor
    processor = DocumentProcessor(config, context, clients)
    processor.process_documents_in_folder(DOCUMENT_FOLDER)
