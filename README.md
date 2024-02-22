# Document Understanding Cloud APIs Example

This code snippet demonstrates how to digitize, classify, and extract documents using UiPath Document Understanding API's.

## Official Documentation

UiPath Document Understanding offers standalone capabilities, allowing integration with external tools and systems through APIs. This release includes APIs for Discovery, Digitization, Classification, Extraction, and Validation. Please take a look at the [Official Documentation](https://docs.uipath.com/document-understanding/automation-cloud/latest/api-guide/example).

## Requirements

- Python 3.11.6
- `requests` library 
- `python-dotenv` library

## Setup

1. Clone the repository to your local machine:

    ```bash
    git clone https://github.com/nvpnathan/DU-Cloud-APIs.git
    ```

2. Navigate to the project directory:

    ```bash
    cd DU-Cloud-APIs
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Set up your environment variables by creating a `.env` file in the root directory and adding the following variables:

  ```env
  APP_ID=
  APP_SECRET=
  AUTH_URL=https://cloud.uipath.com/identity_/connect/token
  BASE_URL=https://cloud.uipath.com/<Cloud Org>/<Cloud Tenant>/du_/api/framework/projects/
  PROJECT_ID=00000000-0000-0000-0000-000000000000
  ```

## Usage

### Processing Documents

1. Place the documents you want to process in the specified folder (`Example Documents` by default).

2. Run the main script `main.py` to process the documents:

    ```bash
    python main.py
    ```

3. Monitor the console output for processing status and any errors.

4. Extracted results will be printed to the console and saved in CSV format in the same folder as the processed documents.

## File Structure

The project structure is organized as follows:
```bash
DU-Cloud-APIs/
│
├── main.py # Main script for document processing
├── auth.py # Authentication class for obtaining bearer token
├── digitize.py # Digitize class for initiating document digitization
├── classify.py # Classify class for document classification
├── extract.py # Extract class for document extraction
├── validate.py # Validate class for document validation
├── result_utils.py # Utility classes for printing and writing extraction results
│
├── .env.example # Example environment variables file
├── requirements.txt # List of dependencies
└── Example Documents/ # Folder containing example documents
```

## TODO
