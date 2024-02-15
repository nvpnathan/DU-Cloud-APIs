# Document Extraction Example

This code snippet demonstrates how to digitize a document and extract fields from it using a machine learning extractor endpoint. In this example, the ML model used is for processing ID cards.

## Usage

This example consists of several functions:

1. `get_bearer_token`: This function retrieves the bearer token required for authentication.

2. `digitize_document`: This function digitizes the input document by making a POST request to a digitization endpoint. It returns the document ID upon successful digitization.

3. `extract_document`: This function extracts fields from the digitized document using a machine learning extractor endpoint. It requires the document ID obtained from the `digitize_document` function.

4. `get_extraction_results`: This function parses the extracted results and prints out the field names, values, and confidence scores.

## Requirements

- Python 3.x
- Requests library (can be installed via `pip install requests`)
- `dotenv` library (can be installed via `pip install python-dotenv`)

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
get_extraction_results()
