import os
import json
import requests
import questionary

CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "extractor_cache.json")


class Discovery:
    def __init__(self, base_url, bearer_token):
        self.base_url = base_url
        self.bearer_token = bearer_token
        self.document_cache = self._load_cache_from_file()

    def _ensure_cache_directory(self):
        """Ensure the cache directory exists."""
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

    def _save_cache_to_file(self, cache_data):
        """Save the cache to a JSON file."""
        self._ensure_cache_directory()
        with open(CACHE_FILE, "w") as cache_file:
            json.dump(cache_data, cache_file)

    def _load_cache_from_file(self):
        """Load the cache from a JSON file or return an empty dict if it doesn't exist."""
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as cache_file:
                return json.load(cache_file)
        return {}

    def get_projects(self):
        cache = {}
        # Check if the cache file exists
        if os.path.exists(CACHE_FILE):
            try:
                # Load the cache
                cache = self._load_cache_from_file()

                # Check if the cache contains the "project" key and it has the required fields
                if cache and "project" in cache and "id" in cache["project"]:
                    use_cache = questionary.confirm(
                        f"Use cached Project: {cache['project']['name']}?"
                    ).ask()
                    if use_cache:
                        project_id = cache["project"]["id"]
                        return project_id
                else:
                    print("Cache file exists, but no valid project data found.")
                    # Handle case where the cache file exists but "project" key is missing or incomplete
                    # Proceed to fetch projects from the API as needed
            except json.JSONDecodeError:
                print("Cache file exists, but it is empty or not valid JSON.")
                # Handle case where the file is blank or contains invalid JSON
        else:
            print("No cache file found. Fetching projects from API.")
            # Handle case where cache file does not exist
            # Proceed to fetch projects from the API

        api_url = f"{self.base_url}?api-version=1"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "text/plain",
        }

        try:
            # Get Projects
            response = requests.get(api_url, headers=headers, timeout=300)

            if response.status_code == 200:
                # Try parsing the JSON response
                try:
                    data = response.json()
                    # Prepare the list of project choices
                    choices = []
                    predefined_choice = "Predefined: Pretrained models to be used for standard scenarios. For custom extractors, create a Project in the Document Understanding app in Automation Cloud."
                    predefined_key = "Predefined"

                    for project in data["projects"]:
                        description = project.get(
                            "description", "No description available"
                        )
                        choice = f"{project['name']}: {description}"
                        if choice.startswith(predefined_key):
                            predefined_choice = choice
                        else:
                            choices.append(choice)

                    # Sort choices alphabetically
                    choices.sort()

                    # Ensure predefined choice is at the top
                    choices.insert(0, predefined_choice)

                    # Prompt the user to select a project
                    selected_project = questionary.select(
                        "Please select a Project:", choices=choices
                    ).ask()

                    # Prompt the user to select a project
                    # answers = prompt(questions)
                    selected_project_name = selected_project.split(":")[0]

                    # Find the selected project details
                    print(selected_project_name)
                    selected_project = next(
                        project
                        for project in data["projects"]
                        if project["name"] == selected_project_name
                    )

                    print(f"Selected Project ID: {selected_project['id']}")
                    print(f"Selected Project Name: {selected_project['name']}")
                    print(
                        f"Selected Project Description: {selected_project.get('description', 'No description available')}"
                    )
                    project_id = selected_project["id"]

                    # Save to cache
                    cache["project"] = {
                        "id": project_id,
                        "name": selected_project["name"],
                    }
                    self._save_cache_to_file(cache)

                    return project_id
                except ValueError as ve:
                    print(f"Error parsing JSON response: {ve}")
            else:
                print(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"An error occurred during getting projects: {e}")

    def get_classifiers(self, project_id):
        # Check if the cache file exists
        if os.path.exists(CACHE_FILE):
            try:
                # Load the cache
                cache = self._load_cache_from_file()

                # Check if the cache contains the "classifier_id" key and it has the required fields
                if (
                    cache
                    and "classifier_id" in cache["project"]
                    and "id" in cache["project"]["classifier_id"]
                ):
                    use_cache = questionary.confirm(
                        f"Use cached Classifier: {cache['project']['classifier_id']['name']}?"
                    ).ask()
                    if use_cache:
                        classifier_id = cache["project"]["classifier_id"]["id"]
                        return classifier_id
                else:
                    print("Cache file exists, but no valid classifier data found.")
                    # Handle case where the cache file exists but "classifier_id" key is missing or incomplete
                    # Proceed to fetch classifier_id from the API as needed
            except json.JSONDecodeError:
                print("Cache file exists, but it is empty or not valid JSON.")
                # Handle case where the file is blank or contains invalid JSON
        else:
            print("No cache file found. Fetching projects from API.")
            # Handle case where cache file does not exist
            # Proceed to fetch projects from the API

        api_url = f"{self.base_url}/{project_id}/classifiers?api-version=1"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "text/plain",
        }

        try:
            # Get Classifiers
            response = requests.get(api_url, headers=headers, timeout=300)

            if response.status_code == 200:
                # Try parsing the JSON response
                try:
                    data = response.json()
                    # Prepare the list of classifiers choices
                    choices = []
                    predefined_choice = "Generative Classifier: Available"
                    predefined_key = "Generative Classifier"

                    # Check if classifiers are present
                    if not data["classifiers"]:
                        print("No classifiers found.")
                        return None

                    for classifier in data["classifiers"]:
                        status = classifier.get("status")
                        choice = f"{classifier['name']}: {status}"
                        if choice.startswith(predefined_key):
                            predefined_choice = choice
                        else:
                            choices.append(choice)

                    # Sort choices alphabetically
                    choices.sort()

                    # Ensure predefined choice is at the top
                    if project_id == "00000000-0000-0000-0000-000000000000":
                        choices.insert(0, predefined_choice)

                    # Prompt the user to select a classifier
                    selected_classifier = questionary.select(
                        "Please select a classifier:", choices=choices
                    ).ask()

                    selected_classifier_name = selected_classifier.split(":")[0]

                    # Find the selected project details
                    selected_classifier = next(
                        classifier
                        for classifier in data["classifiers"]
                        if classifier["name"] == selected_classifier_name
                    )

                    print(f"Selected Classifier ID: {selected_classifier['id']}")
                    print(f"Selected Classifier Name: {selected_classifier['name']}")
                    classifier_id = selected_classifier["id"]
                    if classifier_id == "generative_classifier":
                        prompts_directory = "generative_prompts"
                        prompts_file = os.path.join(
                            prompts_directory, "classification_prompts.json"
                        )
                        if os.path.exists(prompts_file):
                            with open(prompts_file, "r", encoding="utf-8") as file:
                                data = json.load(file)
                                classifier_doc_types = [
                                    item["name"] for item in data["prompts"]
                                ]
                        else:
                            print(f"Error: File '{prompts_file}' not found.")
                            return None
                    else:
                        classifier_doc_types = selected_classifier["documentTypeIds"]

                    # Save to cache
                    cache["project"]["classifier_id"] = {
                        "id": classifier_id,
                        "name": selected_classifier["name"],
                        "doc_type_ids": classifier_doc_types,
                    }
                    self._save_cache_to_file(cache)
                    return classifier_id
                except ValueError as ve:
                    print(f"Error parsing JSON response: {ve}")
            else:
                print(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"An error occurred during getting classifiers: {e}")

    def get_extractors(self, project_id):
        # Check if the cache file exists
        if os.path.exists(CACHE_FILE):
            try:
                # Load the cache
                cache = self._load_cache_from_file()

                # Check if the cache contains the "extractor_ids" key and it has the required fields
                if cache and "extractor_ids" in cache["project"]:
                    use_cache = questionary.confirm("Use cached Extractor(s)?").ask()
                    if use_cache:
                        extractor_dict = cache["project"]["extractor_ids"]
                        return extractor_dict
                else:
                    print("Cache file exists, but no valid extractor data found.")
                    # Handle case where the cache file exists but "classifier_id" key is missing or incomplete
                    # Proceed to fetch classifier_id from the API as needed
            except json.JSONDecodeError:
                print("Cache file exists, but it is empty or not valid JSON.")
                # Handle case where the file is blank or contains invalid JSON
        else:
            print("No cache file found. Fetching projects from API.")
            # Handle case where cache file does not exist
            # Proceed to fetch projects from the API

        api_url = f"{self.base_url}/{project_id}/extractors?api-version=1"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "text/plain",
        }

        try:
            # Get Extractors
            response = requests.get(api_url, headers=headers, timeout=300)
            if response.status_code == 200:
                # Try parsing the JSON response
                try:
                    data = response.json()
                    # Prepare the list of extractors choices
                    choices = []
                    predefined_choice = "Generative Extractor: Available"
                    predefined_key = "Generative Extractor"

                    # Check if extractors are present
                    if not data["extractors"]:
                        print("No extractors found.")
                        return None

                    for extractor in data["extractors"]:
                        status = extractor.get("status")
                        choice = f"{extractor['name']}: {status}"
                        if choice.startswith(predefined_key):
                            predefined_choice = choice
                        else:
                            choices.append(choice)

                    # Sort choices alphabetically
                    choices.sort()

                    # Ensure predefined choice is at the top
                    if project_id == "00000000-0000-0000-0000-000000000000":
                        choices.insert(0, predefined_choice)

                    # Prompt the user to select one or more extractors
                    selected_extractors = questionary.checkbox(
                        "Please select one or more Extractors:", choices=choices
                    ).ask()

                    # Initialize an empty dictionary to store the documentTypeId and corresponding extractor ID
                    extractor_dict = {}

                    # Iterate over the selected extractors and gather their IDs and documentTypeIds
                    for selected_extractor in selected_extractors:
                        selected_extractor_name = selected_extractor.split(":")[0]
                        # Find the matching extractor from the data
                        extractor = next(
                            extractor
                            for extractor in data["extractors"]
                            if extractor["name"] == selected_extractor_name
                        )

                        if extractor["id"] == "generative_extractor":
                            gen_extractor_doc_types = questionary.confirm(
                                "Would you like to add doc types for Generative Extraction?"
                            ).ask()
                            if gen_extractor_doc_types:
                                if (
                                    cache
                                    and "classifier_id" in cache["project"]
                                    and "doc_type_ids"
                                    in cache["project"]["classifier_id"]
                                ):
                                    choices = cache["project"]["classifier_id"][
                                        "doc_type_ids"
                                    ]

                                    selected_gen_ext_doc_types = questionary.checkbox(
                                        "Please select Document Types for Generative Extraction:",
                                        choices=choices,
                                    ).ask()
                                    if selected_gen_ext_doc_types:
                                        extractor_dict[extractor["id"]] = {
                                            "id": extractor["id"],
                                            "name": extractor["name"],
                                            "doc_type_ids": selected_gen_ext_doc_types,
                                        }
                                    else:
                                        extractor_dict[extractor["id"]] = {
                                            "id": extractor["id"],
                                            "name": extractor["name"],
                                            "doc_type_ids": choices,
                                        }

                            else:
                                extractor_dict[extractor["id"]] = {
                                    "id": extractor["id"],
                                    "name": extractor["name"],
                                    "doc_type_ids": ["default_doc"],
                                }

                        else:
                            extractor_dict[extractor["id"]] = {
                                "id": extractor["id"],
                                "name": extractor["name"],
                            }
                    # Save to cache
                    cache["project"]["extractor_ids"] = extractor_dict
                    self._save_cache_to_file(cache)

                    # Return the dictionary with documentTypeId as key and extractor ID as value
                    return extractor_dict
                except ValueError as ve:
                    print(f"Error parsing JSON response: {ve}")
            else:
                print(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"An error occurred during getting extractors: {e}")
