import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from modules.discovery import Discovery, CACHE_FILE, prepare_extractor_choices, build_extractor_dict

class TestDiscovery(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://api.example.com"
        self.bearer_token = "test_token"
        cache_data = {
            "validate_classification": False,
            "validate_extraction": False,
            "perform_classification": True,
            "perform_extraction": True,
            "project": {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": "Predefined",
                "classifier_id": {
                    "id": "ml-classification",
                    "name": "ML Classification",
                    "doc_type_ids": [
                        "id_cards",
                        "invoices"
                    ]
                },
                "extractor_ids": {
                    "id_cards": {
                        "id": "id_cards",
                        "name": "ID Cards"
                    },
                    "invoices": {
                        "id": "invoices",
                        "name": "Invoices"
                    }
                }
            }
        }
        with open(CACHE_FILE, "w") as cache_file:
            json.dump(cache_data, cache_file)

    def tearDown(self):
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)

    #@patch("discovery.questionary.confirm")
    @patch("discovery.Discovery._load_cache_from_file")
    def test_init_with_cached_values(self, mock_load_cache, mock_confirm):
        cache_data = {
            "validate_classification": False,
            "validate_extraction": True,
            "perform_classification": False,
            "perform_extraction": True
        }
        mock_load_cache.return_value = cache_data
        mock_confirm.side_effect = [False, True, False, True]
        discovery = Discovery(self.base_url, self.bearer_token)
        self.assertFalse(discovery.validate_classification)
        self.assertTrue(discovery.validate_extraction)
        self.assertFalse(discovery.perform_classification)
        self.assertTrue(discovery.perform_extraction)

    @patch("questionary.select")
    @patch("requests.get", return_value=MagicMock(status_code=200, json=lambda: {"projects": [{"name": "Test Project", "description": "A test project", "id": "123"}]}))
    def test_get_projects(self, mock_requests, mock_select):
        mock_select.return_value.ask.return_value = "Test Project: A test project"
        discovery = Discovery(self.base_url, self.bearer_token)
        project_id = discovery.get_projects()
        self.assertEqual(project_id, "123")

    @patch("requests.get", return_value=MagicMock(status_code=200, json=lambda: {
        "classifiers": [
            {
                "name": "Test Classifier",
                "status": "Active",
                "id": "456",
                "documentTypeIds": ["id_cards", "invoices"]  # Include this key if required
            }
        ]
    }))
    def test_get_classifiers(self, mock_requests, mock_select):
        mock_select.return_value.ask.return_value = "Test Classifier"
        discovery = Discovery(self.base_url, self.bearer_token)
        classifier_id = discovery.get_classifiers("123")
        self.assertEqual(classifier_id, "456")

    @patch("requests.get", return_value=MagicMock(status_code=200, json=lambda: {
        "extractors": [
            {"name": "Extractor 1", "status": "Available", "id": "789", "documentTypeId": "id_cards"},
            {"name": "Extractor 2", "status": "Unavailable", "id": "790", "documentTypeId": "invoices"}
        ]
    }))
    @patch("questionary.checkbox")
    def test_get_extractors(self, mock_checkbox, mock_requests):
        mock_checkbox.return_value = ["Extractor 1: Available"]
        discovery = Discovery(self.base_url, self.bearer_token)
        extractors = discovery.get_extractors("123")
        self.assertEqual(extractors, [{"name": "Extractor 1", "status": "Available", "id": "789", "documentTypeId": "id_cards"}])

    def test_prepare_extractor_choices(self):
        extractors = [
            {"name": "Extractor 1", "status": "Available", "id": "789"},
            {"name": "Extractor 2", "status": "Unavailable", "id": "790"}
        ]
        choices = prepare_extractor_choices(extractors)
        self.assertEqual(choices, ["Extractor 1: Available"])

    def test_build_extractor_dict(self):
        extractors = [
            {"name": "Extractor 1", "status": "Available", "id": "789", "document_id": "abc"}
        ]
        selected_extractors = ["Extractor 1"]
        cache = {
            "project": {
                "classifier_id": {"doc_type_ids": ["dt1", "dt2"]}
            }
        }
        extractor_dict = build_extractor_dict(extractors, selected_extractors, cache)
        self.assertEqual(extractor_dict, {"abc": {"id": "789", "name": "Extractor 1"}})

    # @patch("discovery.questionary.confirm")
    @patch("discovery.questionary.checkbox")
    def test_build_extractor_dict_with_generative(self, mock_checkbox, mock_confirm):
        extractors = [
            {"name": "Generative Extractor", "status": "Available", "id": "789"}
        ]
        selected_extractors = ["Generative Extractor"]
        cache = {
            "project": {
                "classifier_id": {"doc_type_ids": ["dt1", "dt2"]}
            }
        }
        mock_confirm.return_value = True
        mock_checkbox.return_value = ["dt1"]
        extractor_dict = build_extractor_dict(extractors, selected_extractors, cache)
        self.assertEqual(extractor_dict, {"789": {"id": "789", "name": "Generative Extractor", "doc_type_ids": ["dt1"]}})

if __name__ == "__main__":
    unittest.main()