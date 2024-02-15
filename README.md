# Document Understanding Cloud APIs Example

This code snippet demonstrates how to digitize a document and extract fields from it using a machine learning extractor endpoint. In this example, the ML model used is for processing ID cards.

## Official Documentation

UiPath Document Understanding offers standalone capabilities, allowing integration with external tools and systems through APIs. This release includes APIs for Discovery, Digitization, Classification, Extraction, and Validation. Please take a look at the [Official Documentation](https://docs.uipath.com/document-understanding/automation-cloud/latest/api-guide/example).

## Usage

This example consists of several functions:

1. `get_bearer_token`: This function retrieves the bearer token required for authentication.

2. `digitize_document`: This function digitizes the input document by making a POST request to a digitization endpoint. It returns the document ID upon successful digitization.

3. `classify_document`: This function classifies the digitized document using a machine learning classification endpoint. It requires the document ID obtained from the `digitize_document` function. 

4. `extract_document`: This function extracts fields from the digitized document using a machine learning extractor endpoint. It requires the document ID obtained from the `digitize_document` function.

5. `get_extraction_results`: This function parses the extracted results and prints out the field names, values, and confidence scores.

6. `process_documents_in_folder`: This function wraps all of the functions above and processes all documents within a specified folder

## Requirements

- Python 3.11.6
- `requests` library 
- `python-dotenv` library

## Setup

1. Clone this repository to your local machine.
2. Install the required Python libraries using `pip`:

   `pip install -r requirements.txt`
3. Set up a `.env` file with the following environment variables:

  ```env
  BASE_URL=<UiPath API base URL>
  PROJECT_ID=<Your UiPath project ID>
  APP_ID=<Your UiPath app ID>
  APP_SECRET=<Your UiPath app secret>
  AUTH_URL=<UiPath authentication URL>
  ```

## Usage

1. Place the documents you want to process in the specified document folder.
2. Run the script by executing `python main.py`.
3. The script will process each document in the folder:
- Digitize the document
- Classify the document
- Extract data from the document
4. The extraction results will be written to CSV files in the same folder as the documents.

## Example

```python
import os
import mimetypes
import requests
from dotenv import load_dotenv

load_dotenv()

# Define constants
document_path = "ID Card.jpg"
base_url = os.environ['BASE_URL']
projectId = os.environ['PROJECT_ID']
extractorId = os.environ['EXTRACTOR_ID']
client_id = os.environ['APP_ID']
client_secret = os.environ['APP_SECRET']
token_url = os.environ['AUTH_URL']

# Functions definitions...

# Authenticate and extract results
bearer_token = get_bearer_token(client_id, client_secret, token_url)
process_documents_in_folder()
```

## TODO

* Add validation API support for Action Center
