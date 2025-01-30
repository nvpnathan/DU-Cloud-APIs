# Document Understanding Cloud APIs Example

This project demonstrates how to **digitize**, **classify**, **validate**, and **extract** documents using UiPath Document Understanding API's.

## Official Documentation

UiPath Document Understanding offers standalone capabilities, allowing integration with external tools and systems through APIs. This release includes APIs for Discovery, Digitization, Classification, Extraction, and Validation. Please take a look at the [Official Documentation](https://docs.uipath.com/document-understanding/automation-cloud/latest/api-guide/example).

## Project Features
- Interactive Menu to select your Project, Classifier, and Extractor(s)
- Digitize, Classify, and Extract Documents
- Optional Human In The Loop (HITL)
- Digitization Caching (7 Days)
- Classification CSV results
- Extraction CSV results

## Process Flowchart

![](flowchart.png)

## Requirements

- Python 3.12+
- `requests` library
- `python-dotenv` library
- `questionary` library

## Setup

1. Clone the repository to your local machine:

    ```bash
    git clone https://github.com/nvpnathan/DU-Cloud-APIs.git
    ```

2. Navigate to the project directory:

    ```bash
    cd DU-Cloud-APIs
    ```

3. Create a Python virtual environment:

   ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

5. Install the required dependencies:

    ```bash
    pip3 install -r requirements.txt
    ```

6. Set up your environment variables by copying `.env.example` to `.env` file in the root directory and provide the `APP_ID` and `APP_SECRET` from your Cloud Envirnment:

  ```env
  APP_ID=
  APP_SECRET=
  AUTH_URL=https://cloud.uipath.com/identity_/connect/token
  BASE_URL=https://cloud.uipath.com/<Cloud Org>/<Cloud Tenant>/du_/api/framework/projects/
  ```

## Usage

### Processing Documents

1. Place the documents you want to process in the specified folder (`example_documents` by default).

2. Run the main script `main.py` to process the documents:

    ```bash
    python3 src/main.py
    ```

3. Select your Document Understanding **Project**, **Classifier** (*optional if extracting one document type only*), and **Extractor(s)** (*optional if classifying only*).

4. Monitor the console output for processing status and any errors.

5. **Classification** and **Extraction** results will be printed to the console and saved in CSV format in the `output_results` folder.

## File Structure

The project structure is organized as follows:
```bash
DU-Cloud-APIs/
│
├── src/
│   ├── main.py                  # Main entry point for the application
│   ├── processor.py             # Logic for processing pipeline (should include orchestration, or configuration setup if needed)
│   ├── project_config.py        # Configuration module for project variables and sqlite db creation
│   ├── project_setup.py         # Application-level setup (initialization, environment loading)
│   ├── modules/  
│   │   ├── __init__.py
│   │   ├── digitize.py          # Digitize module for initiating document digitization
│   │   ├── classify.py          # Classify module for document classification
│   │   ├── extract.py           # Extract module for document extraction
│   │   ├── validate.py          # Validate module for document validation
│   │   └── async_request_handler.py  # Module for handling async requests related to validation
│   └── utils/
│       ├── auth.py              # Authentication module for obtaining bearer token
│       └── write_results.py     # Utility module for writing classification and extraction results to SQLite
├── tests/
│   ├── test_main.py      # Test for the main application entry point
│   ├── test_digitize.py  # Test for the document digitization module
│   ├── test_discovery.py # Test for the document discovery module
│   ├── test_classify.py  # Test for the document classification module
│   ├── test_extract.py   # Test for the document extraction module
│   └── test_validate.py  # Test for the document validation module
│
├── .env.example         # Example environment variables file
├── requirements.txt     # Python modules configuration file
├── example_documents/   # Folder containing example documents
├── generative_prompts/  # Folder containing Extraction and Classification Prompt Templates
└── output_results/      # Folder containing the CSV's of the Document Extraction Results
```

## SQLite Usage

This project uses SQLite to store and manage various document processing results. The database schema includes the following tables:

1. **documents**: Stores metadata and processing stages for each document.
    - `document_id`: Unique identifier for the document.
    - `filename`: Name of the document file.
    - `stage`: Current processing stage of the document.
    - `timestamp`: Timestamp of the last update.
    - `document_type_id`: Type of the document.
    - `digitization_operation_id`: Operation ID for digitization.
    - `classification_operation_id`: Operation ID for classification.
    - `classification_validation_operation_id`: Operation ID for classification validation.
    - `extraction_operation_id`: Operation ID for extraction.
    - `extraction_validation_operation_id`: Operation ID for extraction validation.
    - `digitization_duration`: Duration of the digitization process.
    - `classification_duration`: Duration of the classification process.
    - `classification_validation_duration`: Duration of the classification validation process.
    - `extraction_duration`: Duration of the extraction process.
    - `extraction_validation_duration`: Duration of the extraction validation process.
    - `project_id`: Identifier for the project used.
    - `classifier_id`: Identifier for the classifier used.
    - `extractor_id`: Identifier for the extractor used.
    - `error_code`: Error code if any error occurred.
    - `error_message`: Error message if any error occurred.

2. **classification**: Stores classification results for each document.
    - `id`: Auto-incremented primary key.
    - `document_id`: Unique identifier for the document.
    - `filename`: Name of the document file.
    - `document_type_id`: Type of the document.
    - `classification_confidence`: Confidence score of the classification.
    - `start_page`: Starting page of the classified section.
    - `page_count`: Number of pages in the classified section.
    - `classifier_name`: Name of the classifier used.
    - `operation_id`: Operation ID for the classification.

3. **extraction**: Stores extraction results for each document.
    - `filename`: Name of the document file.
    - `document_id`: Unique identifier for the document.
    - `document_type_id`: Type of the document.
    - `field_id`: Identifier for the field.
    - `field`: Name of the field.
    - `is_missing`: Boolean indicating if the field is missing.
    - `field_value`: Extracted value of the field.
    - `field_unformatted_value`: Unformatted extracted value of the field.
    - `validated_field_value`: Validated value of the field.
    - `is_correct`: Boolean indicating if the extracted value is correct.
    - `confidence`: Confidence score of the extraction.
    - `ocr_confidence`: OCR confidence score of the extraction.
    - `operator_confirmed`: Boolean indicating if the value was confirmed by an operator.
    - `row_index`: Row index for table fields (default -1).
    - `column_index`: Column index for table fields (default -1).
    - `timestamp`: Timestamp of the extraction (default CURRENT_TIMESTAMP).
    - `PRIMARY KEY (filename, field_id, field, row_index, column_index)`.

These tables are created and managed in the [`ensure_database`](src/config.py) function in [src/config.py](src/config.py).

## TODO

&#9744; Write Tests for Discovery API

&#9744; Perform validation outside of the workflow (optional)

&#9744; Add unique batch_id for each run

&#9745; Create CSV output files from sqlite results

&#9745; Bumped DU REST API version to `1.1`

&#9745; Moved Async requests to `api_utils.py`

&#9745; Added sqlite tables (`documents`, `classification`, `extraction`) for all classification, extraction, and validation results

&#9745; Write initial tests for core
