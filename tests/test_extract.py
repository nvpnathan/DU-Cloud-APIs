import os
import sys
import unittest
from unittest.mock import Mock
from requests.exceptions import RequestException
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from extract import Extract


class TestExtract(unittest.TestCase):

    def test_extract_document_successful(self):
        base_url = "https://example.com/"
        project_id = "project123"
        bearer_token = "bearerToken"
        document_id = "12345"
        extractor_id = "test_extractor"
        prompts = {"prompt1": "value1", "prompt2": "value2"}

        # Mock response for the POST request
        response_data = {"key1": "value1", "key2": "value2"}
        response = Mock()
        response.status_code = 200
        response.json.return_value = response_data

        with unittest.mock.patch('requests.post', return_value=response) as mock_post:
            extractor = Extract(base_url, project_id, bearer_token)
            extracted_data = extractor.extract_document(extractor_id, document_id, prompts=prompts)

            self.assertEqual(extracted_data, response_data)
            mock_post.assert_called_once()

    def test_extract_document_failed(self):
        base_url = "https://example.com/"
        project_id = "project123"
        bearer_token = "bearerToken"
        document_id = "12345"
        extractor_id = "test_extractor"
        prompts = {"prompt1": "value1", "prompt2": "value2"}

        # Mock response for the POST request
        response = Mock()
        response.status_code = 500

        with unittest.mock.patch('requests.post', return_value=response) as mock_post:
            extractor = Extract(base_url, project_id, bearer_token)
            extracted_data = extractor.extract_document(extractor_id, document_id, prompts=prompts)

            self.assertIsNone(extracted_data)
            mock_post.assert_called_once()

    def test_extract_document_exception(self):
        base_url = "https://example.com/"
        project_id = "project123"
        bearer_token = "bearerToken"
        document_id = "12345"
        extractor_id = "test_extractor"
        prompts = {"prompt1": "value1", "prompt2": "value2"}

        with unittest.mock.patch('requests.post', side_effect=RequestException) as mock_post:
            extractor = Extract(base_url, project_id, bearer_token)
            extracted_data = extractor.extract_document(extractor_id, document_id, prompts=prompts)

            self.assertIsNone(extracted_data)
            mock_post.assert_called_once()


if __name__ == '__main__':
    unittest.main()
