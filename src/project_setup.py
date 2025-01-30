import os
import json
import sqlite3
from dotenv import load_dotenv
from modules import Digitize, Classify, Extract, Validate, Discovery
from utils.auth import initialize_authentication
from project_config import (
    ProcessingConfig,
    DocumentProcessingContext,
    BASE_URL,
    CACHE_DIR,
    SQLITE_DB_PATH,
)


# Load environment variables
load_dotenv()

# Initialize Authentication
auth = initialize_authentication()
bearer_token = auth.bearer_token
base_url = os.getenv("BASE_URL")


def ensure_cache_directory():
    """Ensure the cache directory exists."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def ensure_database():
    """Ensure the SQLite database and required tables exist."""
    ensure_cache_directory()

    # Check if the database file exists
    if not os.path.exists(SQLITE_DB_PATH):
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Create documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                stage TEXT NOT NULL,
                digitization_operation_id TEXT,
                classification_operation_id TEXT,
                classification_validation_operation_id TEXT,
                extraction_operation_id TEXT,
                extraction_validation_operation_id TEXT,
                digitization_duration REAL,
                classification_duration REAL,
                classification_validation_duration REAL,
                extraction_duration REAL,
                extraction_validation_duration REAL,
                project_id TEXT,
                classifier_id TEXT,
                extractor_id TEXT,
                error_code TEXT,
                error_message TEXT,
                timestamp REAL NOT NULL
            )
        """)

        # Create classification table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                document_type_id TEXT NOT NULL,
                classification_confidence REAL NOT NULL,
                start_page INTEGER NOT NULL,
                page_count INTEGER NOT NULL,
                classifier_name TEXT NOT NULL,
                operation_id TEXT NOT NULL
            )
        """)

        # Create extraction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extraction (
                filename TEXT NOT NULL,
                document_id TEXT NOT NULL,
                document_type_id TEXT NOT NULL,
                field_id TEXT,
                field TEXT,
                is_missing BOOLEAN,
                field_value TEXT,
                field_unformatted_value TEXT,
                validated_field_value TEXT,
                is_correct BOOLEAN,
                confidence REAL,
                ocr_confidence REAL,
                operator_confirmed BOOLEAN,
                row_index INTEGER DEFAULT -1,
                column_index INTEGER DEFAULT -1,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (filename, field_id, field, row_index, column_index)
            )
        """)

        conn.commit()
        conn.close()


# Function to initialize clients
def initialize_clients(
    context: DocumentProcessingContext, base_url: str, bearer_token: str
):
    digitize_client = Digitize(base_url, context.project_id, bearer_token)
    classify_client = Classify(base_url, context.project_id, bearer_token)
    extract_client = Extract(base_url, context.project_id, bearer_token)
    validate_client = Validate(base_url, context.project_id, bearer_token)

    return digitize_client, classify_client, extract_client, validate_client


def load_endpoints(discovery_client, load_classifier, load_extractor):
    """Load project and optional classifier/extractor information."""
    project_id = discovery_client.get_projects()

    # Conditionally load classifiers and extractors based on flags
    classifier = (
        discovery_client.get_classifiers(project_id) if load_classifier else None
    )
    extractor_dict = (
        discovery_client.get_extractors(project_id) if load_extractor else None
    )

    return project_id, classifier, extractor_dict


def get_processing_config(discovery_client):
    """Retrieve configuration with boolean flags managed by Discovery."""
    # Initialize ProcessingConfig with values retrieved by Discovery
    return ProcessingConfig(
        validate_classification=discovery_client.validate_classification,
        validate_extraction=discovery_client.validate_extraction,
        perform_classification=discovery_client.perform_classification,
        perform_extraction=discovery_client.perform_extraction,
    )


def load_prompts(document_type_id: str) -> dict | None:
    """Load prompts from a JSON file based on the document type ID."""
    prompts_directory = "generative_prompts"
    prompts_file = os.path.join(prompts_directory, f"{document_type_id}_prompts.json")
    if os.path.exists(prompts_file):
        with open(prompts_file, "r", encoding="utf-8") as file:
            return json.load(file)
    else:
        print(f"Error: File '{prompts_file}' not found.")
        return None


def initialize_environment():
    """Initialize the processing environment."""
    # Load environment variables
    load_dotenv()

    # Ensure database exists
    ensure_database()

    discovery_client = Discovery(BASE_URL, bearer_token)

    # Load endpoints
    project_id, classifier, extractor_dict = load_endpoints(
        discovery_client,
        load_classifier=True,
        load_extractor=True,
    )

    # Create context and config
    context = DocumentProcessingContext(
        project_id=project_id,
        classifier=classifier,
        extractor_dict=extractor_dict,
    )
    config = get_processing_config(discovery_client)

    # Initialize clients
    clients = initialize_clients(context, BASE_URL, bearer_token)

    return config, context, clients
