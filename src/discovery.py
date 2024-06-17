import requests
from InquirerPy import prompt


class Discovery:
    def __init__(self, base_url, bearer_token):
        self.base_url = base_url
        self.bearer_token = bearer_token

    def get_projects(self):
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

                    # Define the question for project selection
                    questions = [
                        {
                            "type": "list",
                            "name": "selected_project",
                            "message": "Please select a project:",
                            "choices": choices,
                        }
                    ]

                    # Prompt the user to select a project
                    answers = prompt(questions)
                    selected_project_name = answers["selected_project"].split(":")[0]

                    # Find the selected project details
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
                    return project_id
                except ValueError as ve:
                    print(f"Error parsing JSON response: {ve}")
            else:
                print(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"An error occurred during getting projects: {e}")

    def get_classifers(self, project_id):
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
                        return

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

                    # Define the question for classifier selection
                    questions = [
                        {
                            "type": "list",
                            "name": "selected_classifier",
                            "message": "Please select a classifier:",
                            "choices": choices,
                        }
                    ]

                    # Prompt the user to select a classifier
                    answers = prompt(questions)
                    selected_classifier_name = answers["selected_classifier"].split(
                        ":"
                    )[0]

                    # Find the selected project details
                    selected_classifier = next(
                        classifier
                        for classifier in data["classifiers"]
                        if classifier["name"] == selected_classifier_name
                    )

                    print(f"Selected Classifier ID: {selected_classifier['id']}")
                    print(f"Selected Classifier Name: {selected_classifier['name']}")
                    classifier_url = selected_classifier["asyncUrl"]

                    return classifier_url
                except ValueError as ve:
                    print(f"Error parsing JSON response: {ve}")
            else:
                print(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"An error occurred during getting classifiers: {e}")

    def get_extractors(self, project_id):
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
                        return

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

                    # Define the question for extractor selection
                    questions = [
                        {
                            "type": "list",
                            "name": "selected_extractor",
                            "message": "Please select an extractor:",
                            "choices": choices,
                        }
                    ]

                    # Prompt the user to select a extractor
                    answers = prompt(questions)
                    selected_extractor_name = answers["selected_extractor"].split(":")[
                        0
                    ]

                    # Find the selected project details
                    selected_extractor = next(
                        extractor
                        for extractor in data["extractors"]
                        if extractor["name"] == selected_extractor_name
                    )

                    print(f"Selected Extractor ID: {selected_extractor['id']}")
                    print(f"Selected Extractor Name: {selected_extractor['name']}")
                    extractor_url = selected_extractor["asyncUrl"]
                    return extractor_url
                except ValueError as ve:
                    print(f"Error parsing JSON response: {ve}")
            else:
                print(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"An error occurred during getting extractors: {e}")
