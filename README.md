# Document Understanding Cloud APIs Example

This code snippet demonstrates how to digitize, classify, validate, and extract documents using UiPath Document Understanding API's.

## Official Documentation

UiPath Document Understanding offers standalone capabilities, allowing integration with external tools and systems through APIs. This release includes APIs for Discovery, Digitization, Classification, Extraction, and Validation. Please take a look at the [Official Documentation](https://docs.uipath.com/document-understanding/automation-cloud/latest/api-guide/example).


## Process Flowchart

![](flowchart.png)

## Requirements

- Python 3.11+
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

3. Select your Document Understanding **Project**, **Classifier** (*optional if extracting one document type only*), an **Extractor(s)** (*optional if classifying only*).

4. Monitor the console output for processing status and any errors.

5. Extracted results will be printed to the console and saved in CSV format in the `output_results` folder.

## File Structure

The project structure is organized as follows:
```bash
DU-Cloud-APIs/
│
├── src/
│   ├── main.py         # Main entry point for the application
│   ├── auth.py         # Authentication module for obtaining bearer token
│   ├── digitize.py     # Digitize module for initiating document digitization
│   ├── classify.py     # Classify module for document classification
│   ├── extract.py      # Extract module for document extraction
│   ├── validate.py     # Validate module for document validation
│   ├── config.py       # Configuration module for project variables
│   └── result_utils.py # Utility module for printing and writing extraction results
│
├── tests/
│   ├── test_main.py     # Test for the main application entry point
│   ├── test_digitize.py # Test for the document digitization module
│   ├── test_classify.py # Test for the document classification module
│   ├── test_extract.py  # Test for the document extraction module
│   └── test_validate.py # Test for the document validation module
│
├── .env.example         # Example environment variables file
├── requirements.txt     # Python modules configuration file
├── example_documents/   # Folder containing example documents
├── generative_prompts/  # Folder containing Extraction and Classification Prompt Templates
└── output_results/      # Folder containing the CSV's of the Document Extraction Results
```

## TODO

&#9744; Write Tests for Discovery API

&#9744; Write Output CSV for Classification

&#9745; Add Ruff for linting

&#9745; Write initial tests for core
