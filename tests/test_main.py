import unittest
from unittest.mock import patch
from main import process_document, process_documents_in_folder


class TestMain(unittest.TestCase):
    @patch("main.digitize_client")
    @patch("main.classify_client")
    @patch("main.extract_client")
    @patch("main.validate_client")
    @patch("main.CSVWriter")
    @patch("main.load_prompts")
    def test_process_document(
        self,
        mock_load_prompts,
        mock_CSVWriter,
        mock_validate_client,
        mock_extract_client,
        mock_classify_client,
        mock_digitize_client,
    ):
        mock_digitize_client.digitize.return_value = "DOC123"
        mock_classify_client.classify_document.return_value = "TypeID123"
        mock_load_prompts.side_effect = [{"prompt1": "value1"}]
        mock_extract_client.extract_document.return_value = {"key1": "value1"}

        process_document(
            "test_document.pdf", "output_directory", True, False, True, False
        )

        mock_digitize_client.digitize.assert_called_once_with("test_document.pdf")
        mock_classify_client.classify_document.assert_called_once_with(
            "DOC123", "generative_classifier", {"prompt1": "value1"}, True
        )
        mock_extract_client.extract_document.assert_called_once()

    @patch("main.os.listdir")
    @patch("main.process_document")
    def test_process_documents_in_folder(self, mock_process_document, mock_listdir):
        mock_listdir.return_value = ["doc1.pdf", "doc2.png"]

        process_documents_in_folder(
            "test_folder", "output_directory", True, True, False, False
        )

        self.assertEqual(mock_process_document.call_count, 2)
        mock_process_document.assert_any_call(
            "test_folder/doc1.pdf", "output_directory", True, True, False, False
        )
        mock_process_document.assert_any_call(
            "test_folder/doc2.png", "output_directory", True, True, False, False
        )


if __name__ == "__main__":
    unittest.main()
