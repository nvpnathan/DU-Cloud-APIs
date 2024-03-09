import os
import sys
import unittest
from unittest.mock import Mock
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from classify import Classify


class TestClassify(unittest.TestCase):

    def test_classify_document_successful(self):
        base_url = "https://example.com/"
        project_id = "project123"
        bearer_token = "bearerToken"
        document_id = "12345"
        classifier = "test_classifier"
        classification_prompts = {"prompt1": "value1", "prompt2": "value2"}

        # Mock response for the POST request
        response_data = {
            "classificationResults": [
                {"DocumentId": "12345", "DocumentTypeId": "doc_type_1", "Confidence": 0.95}
            ]
        }
        response = Mock()
        response.status_code = 200
        response.json.return_value = response_data

        with unittest.mock.patch('requests.post', return_value=response) as mock_post:
            classifier = Classify(base_url, project_id, bearer_token)
            result = classifier.classify_document(document_id, classifier, classification_prompts, validate_classification=False)

            self.assertEqual(result, 'doc_type_1')
            mock_post.assert_called_once()

    def test_classify_document_failed(self):
        base_url = "https://example.com/"
        project_id = "project123"
        bearer_token = "bearerToken"
        document_id = "12345"
        classifier = "test_classifier"
        classification_prompts = {"prompt1": "value1", "prompt2": "value2"}

        # Mock response for the POST request
        response = Mock()
        response.status_code = 400

        with unittest.mock.patch('requests.post', return_value=response) as mock_post:
            classifier = Classify(base_url, project_id, bearer_token)
            result = classifier.classify_document(document_id, classifier, classification_prompts, validate_classification=False)

            self.assertIsNone(result)
            mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main()