import os
from dotenv import load_dotenv

# Define the path to the configuration file
CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "document_cache.json")
CACHE_EXPIRY_DAYS = 7
SQLITE_DB_PATH = os.path.join(CACHE_DIR, "document_cache.db")

# Load environment variables
load_dotenv()
BASE_URL = os.getenv("BASE_URL")


class ProcessingConfig:
    """
    Configuration class for controlling various document processing steps.

    Attributes:
        validate_classification (bool): Whether to validate classification results.
        validate_extraction (bool): Whether to validate extraction results.
        validate_extraction_later (bool): Whether to defer extraction validation (only applicable if validate_extraction is True).
        perform_classification (bool): Whether to perform classification as part of the pipeline.
        perform_extraction (bool): Whether to perform extraction as part of the pipeline.
    """

    def __init__(
        self,
        validate_classification: bool = False,
        validate_extraction: bool = False,
        validate_extraction_later: bool = False,
        perform_classification: bool = True,
        perform_extraction: bool = True,
    ):
        self.validate_classification: bool = validate_classification
        self.validate_extraction: bool = validate_extraction
        self.validate_extraction_later: bool = (
            validate_extraction_later if validate_extraction else False
        )
        self.perform_classification: bool = perform_classification
        self.perform_extraction: bool = perform_extraction


class DocumentProcessingContext:
    """
    Context class for managing document processing information.

    Attributes:
        project_id (str): The unique identifier for the project.
        classifier (str | None): The name of the classifier to use, if applicable.
        extractor_dict (dict | None): A dictionary of extractors and their configurations.
    """

    def __init__(
        self,
        project_id: str,
        classifier: str | None = None,
        extractor_dict: dict | None = None,
    ):
        self.project_id: str = project_id
        self.classifier: str | None = classifier
        self.extractor_dict: dict | None = extractor_dict
