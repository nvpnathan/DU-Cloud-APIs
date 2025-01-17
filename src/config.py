import os
import json
import sqlite3

# Cache configuration
CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "document_cache.json")
SQLITE_DB_PATH = os.path.join(CACHE_DIR, "document_cache.db")
CACHE_EXPIRY_DAYS = 7  # Cache expiry in days


class ProcessingConfig:
    def __init__(
        self,
        validate_classification=False,
        validate_extraction=False,
        perform_classification=True,
        perform_extraction=True,
    ):
        self.validate_classification = validate_classification
        self.validate_extraction = validate_extraction
        self.perform_classification = perform_classification
        self.perform_extraction = perform_extraction


class DocumentProcessingContext:
    def __init__(self, project_id, classifier=None, extractor_dict=None):
        self.project_id = project_id
        self.classifier = classifier
        self.extractor_dict = extractor_dict


def load_env_file(filepath=".env"):
    """Load environment variables from a .env file."""
    if os.path.isfile(filepath):
        with open(filepath) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value.strip('"').strip("'")


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


# Function to load prompts from a JSON file based on the document type ID
def load_prompts(document_type_id: str) -> dict | None:
    prompts_directory = "generative_prompts"
    prompts_file = os.path.join(prompts_directory, f"{document_type_id}_prompts.json")
    if os.path.exists(prompts_file):
        with open(prompts_file, "r", encoding="utf-8") as file:
            return json.load(file)
    else:
        print(f"Error: File '{prompts_file}' not found.")
        return None


def ensure_database():
    """Ensure the SQLite database and required tables exist."""
    # Ensure the cache directory exists
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

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
                timestamp REAL NOT NULL,
                document_type_id TEXT,
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
                error_code TEXT,
                error_message TEXT
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
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
