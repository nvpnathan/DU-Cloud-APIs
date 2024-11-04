import os
import json
import sqlite3
from discovery import Discovery

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


# Function to select your Classifier and/or Extractor(s)
def load_endpoints(load_classifier, load_extractor, base_url, bearer_token):
    discovery_client = Discovery(base_url, bearer_token)
    project_id = discovery_client.get_projects()

    # Conditionally load classifiers and extractors based on flags
    classifier = (
        discovery_client.get_classifiers(project_id) if load_classifier else None
    )
    extractor_dict = (
        discovery_client.get_extractors(project_id) if load_extractor else None
    )

    return project_id, classifier, extractor_dict


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
                classify_operation_id TEXT,
                extract_operation_id TEXT,
                digitize_duration REAL,
                classification_duration REAL,
                extract_duration REAL
            )
        """)

        # Create classifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classifications (
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

        conn.commit()
        conn.close()
