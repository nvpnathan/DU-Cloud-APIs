import os
import sys
import unittest
from unittest.mock import Mock
from requests.exceptions import RequestException

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from modules.validate import Validate


class TestValidate(unittest.TestCase):
    def test_validate_extraction_results_successful(self):
        base_url = "https://example.com/"
        project_id = "project123"
        bearer_token = "bearerToken"
        document_id = "12345"
        extractor_id = "test_extractor"
        extraction_results = {"prompt1": "value1", "prompt2": "value2"}
        extraction_prompts = {"prompt3": "value3", "prompt4": "value4"}

        # Mock response for the POST request
        response_data = {"key1": "value1", "key2": "value2"}
        response = Mock()
        response.status_code = 202
        response.json.return_value = response_data

        with unittest.mock.patch(
            "requests.post", return_value=response
        ) as mock_post, unittest.mock.patch.object(
            Validate, "submit_extraction_validation_request", return_value=response_data
        ) as mock_submit:
            validator = Validate(base_url, project_id, bearer_token)
            validated_results = validator.validate_extraction_results(
                extractor_id, document_id, extraction_results, extraction_prompts
            )

            self.assertEqual(validated_results, response_data)
            mock_post.assert_called_once()
            mock_submit.assert_called_once()

    def test_validate_extraction_results_failed(self):
        base_url = "https://example.com/"
        project_id = "project123"
        bearer_token = "bearerToken"
        document_id = "12345"
        extractor_id = "test_extractor"
        extraction_results = {"prompt1": "value1", "prompt2": "value2"}
        extraction_prompts = {"prompt3": "value3", "prompt4": "value4"}

        # Mock response for the POST request
        response = Mock()
        response.status_code = 400

        with unittest.mock.patch("requests.post", return_value=response) as mock_post:
            validator = Validate(base_url, project_id, bearer_token)
            validated_results = validator.validate_extraction_results(
                extractor_id, document_id, extraction_results, extraction_prompts
            )

            self.assertIsNone(validated_results)
            mock_post.assert_called_once()

    def test_validate_extraction_results_exception(self):
        base_url = "https://example.com/"
        project_id = "project123"
        bearer_token = "bearerToken"
        document_id = "12345"
        extractor_id = "test_extractor"
        extraction_results = {"prompt1": "value1", "prompt2": "value2"}
        extraction_prompts = {"prompt3": "value3", "prompt4": "value4"}

        with unittest.mock.patch(
            "requests.post", side_effect=RequestException
        ) as mock_post:
            validator = Validate(base_url, project_id, bearer_token)
            validated_results = validator.validate_extraction_results(
                extractor_id, document_id, extraction_results, extraction_prompts
            )

            self.assertIsNone(validated_results)
            mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
