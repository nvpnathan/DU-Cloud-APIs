import os
import sys
import unittest
from unittest.mock import Mock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from modules.digitize import Digitize


class TestDigitize(unittest.TestCase):
    def test_digitize_successful(self):
        base_url = "https://example.com/"
        project_id = "project123"
        bearer_token = "bearerToken"

        # Mock response for the POST request
        post_response = Mock()
        post_response.status_code = 202
        post_response.json.return_value = {"documentId": "12345"}

        # Mock response for the GET request
        get_response = Mock()
        get_response.json.return_value = {
            "status": "Succeeded",
            "result": {"documentObjectModel": {"documentId": "12345"}},
        }

        with unittest.mock.patch(
            "requests.post", return_value=post_response
        ) as mock_post, unittest.mock.patch(
            "requests.get", return_value=get_response
        ) as mock_get:
            digitizer = Digitize(base_url, project_id, bearer_token)
            digitize_results = digitizer.digitize("./example_documents/id_card.jpg")

            self.assertEqual(digitize_results, "12345")
            mock_post.assert_called_once()
            mock_get.assert_called_once()

    def test_digitize_failed(self):
        base_url = "https://example.com/"
        project_id = "project123"
        bearer_token = "bearerToken"

        # Mock response for the POST request
        post_response = Mock()
        post_response.status_code = 400

        with unittest.mock.patch(
            "requests.post", return_value=post_response
        ) as mock_post:
            digitizer = Digitize(base_url, project_id, bearer_token)
            digitize_results = digitizer.digitize("./example_documents/id_card.jpg")

            self.assertIsNone(digitize_results)
            mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
