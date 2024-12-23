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

        # Retrieve boolean values from cache or prompt the user
        self.validate_classification = self._get_cached_boolean(
            "validate_classification", "Validate classification?"
        )
        self.validate_extraction = self._get_cached_boolean(
            "validate_extraction", "Validate extraction?"
        )
        self.perform_classification = self._get_cached_boolean(
            "perform_classification", "Perform classification?"
        )
        self.perform_extraction = self._get_cached_boolean(
            "perform_extraction", "Perform extraction?"
        )

        # Save updated cache values
        self._save_cache_to_file(self.document_cache)

    def _ensure_cache_directory(self):
        """Ensure the cache directory exists."""
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

    def _save_cache_to_file(self, cache_data):
        """Save the cache to a JSON file."""
        self._ensure_cache_directory()
        with open(CACHE_FILE, "w") as cache_file:
            json.dump(cache_data, cache_file, indent=4)

    def _load_cache_from_file(self):
        """Load the cache from a JSON file or return an empty dict if it doesn't exist."""
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as cache_file:
                return json.load(cache_file)
        return {}

    def _get_cached_boolean(self, cache_key, question_text):
        """Retrieve a cached boolean value or prompt the user if not in cache."""
        if cache_key in self.document_cache:
            cached_value = self.document_cache[cache_key]
            user_value = questionary.confirm(question_text, default=cached_value).ask()

            self.document_cache[cache_key] = user_value
            self._save_cache_to_file(self.document_cache)  # Save to file
            return user_value

        # Prompt the user for a new value if not in cache and update cache
        new_value = questionary.confirm(question_text).ask()
        self.document_cache[cache_key] = new_value
        self._save_cache_to_file(self.document_cache)  # Save to file
        return new_value

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
                if cache and "extractor_ids" in cache.get("project", {}):
                    extractor_names = [
                        extractor["name"]
                        for extractor in cache["project"]["extractor_ids"].values()
                    ]
                    use_cache = questionary.confirm(
                        f"""Use cached Extractor(s):\n {',\n'.join(extractor_names)}\n?"""
                    ).ask()
                    if use_cache:
                        return cache["project"]["extractor_ids"]
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
            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                return None

            # Try parsing the JSON response
            try:
                data = response.json()
            except ValueError as ve:
                print(f"Error parsing JSON response: {ve}")
                return None

            if not data.get("extractors"):
                print("No extractors found.")
                return None

            choices, predefined_choice = prepare_extractor_choices(data["extractors"])

            # Ensure predefined choice is at the top for specific project ID
            if project_id == "00000000-0000-0000-0000-000000000000":
                choices.insert(0, predefined_choice)

            # Prompt the user to select one or more extractors
            selected_extractors = questionary.checkbox(
                "Please select one or more Extractors:", choices=choices
            ).ask()

            # Build the extractor dictionary based on user selections
            extractor_dict = build_extractor_dict(
                data["extractors"], selected_extractors, cache
            )

            # Save to cache and return
            cache["project"]["extractor_ids"] = extractor_dict
            self._save_cache_to_file(cache)
            return extractor_dict

        except Exception as e:
            print(f"An error occurred during getting extractors: {e}")
            return None


def prepare_extractor_choices(extractors):
    """Prepares the list of choices and handles the predefined choice."""
    choices = []
    predefined_choice = "Generative Extractor: Available"
    predefined_key = "Generative Extractor"

    for extractor in extractors:
        status = extractor.get("status", "Unknown")
        if status == "Available":
            choice = f"{extractor['name']}: {status}"
            if choice.startswith(predefined_key):
                predefined_choice = choice
            else:
                choices.append(choice)

    choices.sort()
    return choices, predefined_choice


def build_extractor_dict(extractors, selected_extractors, cache):
    """Creates a dictionary of selected extractors with their document types."""
    extractor_dict = {}
    for selected_extractor in selected_extractors:
        selected_extractor_name = selected_extractor.split(":")[0]

        # Find the matching extractor from the data
        extractor = next(
            (ext for ext in extractors if ext["name"] == selected_extractor_name), None
        )
        if not extractor:
            continue  # Skip if no matching extractor is found

        # Handle generative extractor document types
        if extractor["id"] == "generative_extractor":
            handle_generative_extractor(extractor, cache, extractor_dict)
        else:
            extractor_dict[extractor["documentTypeId"]] = {
                "id": extractor["id"],
                "name": extractor["name"],
            }

    return extractor_dict


def handle_generative_extractor(extractor, cache, extractor_dict):
    """Prompts the user for document types for the generative extractor."""
    gen_extractor_doc_types = questionary.confirm(
        "Would you like to add doc types for Generative Extraction?"
    ).ask()

    if gen_extractor_doc_types and cache:
        doc_type_choices = (
            cache.get("project", {}).get("classifier_id", {}).get("doc_type_ids", [])
        )
        selected_gen_ext_doc_types = (
            questionary.checkbox(
                "Please select Document Types for Generative Extraction:",
                choices=doc_type_choices,
            ).ask()
            or doc_type_choices
        )  # Use all choices if none selected
        extractor_dict[extractor["id"]] = {
            "id": extractor["id"],
            "name": extractor["name"],
            "doc_type_ids": selected_gen_ext_doc_types,
        }
    else:
        # Use default document type if no selection is made
        extractor_dict[extractor["id"]] = {
            "id": extractor["id"],
            "name": extractor["name"],
            "doc_type_ids": ["default_doc"],
        }
