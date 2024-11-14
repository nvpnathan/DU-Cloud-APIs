import os
import time
import requests
import threading
from config import load_env_file
from urllib.parse import urlparse

# Load environment variables
load_env_file()


class Authentication:
    def __init__(self, app_id, app_secret, auth_url):
        self.app_id = app_id
        self.app_secret = app_secret
        self.auth_url = auth_url
        self.bearer_token = None
        self.token_expiry = None
        self.refresh_token()  # Fetch initial token

    def get_bearer_token(self) -> str | None:
        # Check if token is already obtained and not expired
        if self.bearer_token and self.token_expiry and time.time() < self.token_expiry:
            return self.bearer_token

        data = {
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "grant_type": "client_credentials",
            "scope": (
                "Du.DocumentManager.Document "
                "Du.Classification.Api "
                "Du.Digitization.Api "
                "Du.Extraction.Api "
                "Du.Validation.Api"
            ),
        }

        try:
            # Make the POST request to obtain the token
            response = requests.post(self.auth_url, data=data, timeout=30)
            response.raise_for_status()  # Raise an exception for HTTP errors

            token_data = response.json()

            # Extract and store the access token and its expiry time
            self.bearer_token = token_data.get("access_token")
            self.token_expiry = time.time() + token_data.get("expires_in", 3600)

            if self.bearer_token:
                print("Authenticated!\n")
                return self.bearer_token
            else:
                print("Error: No access token received")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching token: {e}")
            return None

    def refresh_token(self):
        # Call get_bearer_token to refresh the token
        self.bearer_token = self.get_bearer_token()

    def token_validity_duration(self):
        # Return the remaining validity duration of the token
        if self.token_expiry:
            return max(0, self.token_expiry - time.time())
        else:
            return 0


# Function to periodically refresh the bearer token
def token_refresh_scheduler(auth_instance):
    while True:
        time.sleep(auth_instance.token_validity_duration() / 2)
        auth_instance.refresh_token()


# Function to initialize authentication and start the refresh thread
def initialize_authentication():
    # Retrieve environment variables
    app_id = os.getenv("APP_ID")
    app_secret = os.getenv("APP_SECRET")
    auth_url = os.getenv("AUTH_URL")

    # Validate APP_ID and APP_SECRET are not None
    if not app_id or not app_secret:
        raise ValueError(
            "APP_ID and APP_SECRET must not be None. Please set these environment variables."
        )

    # Validate AUTH_URL
    parsed_url = urlparse(auth_url)
    if not (parsed_url.scheme and parsed_url.netloc):
        raise ValueError("AUTH_URL is not a valid URL. Please provide a valid URL.")

    # Initialize Authentication
    auth = Authentication(app_id, app_secret, auth_url)

    # Create a daemon thread for token refresh
    refresh_thread = threading.Thread(target=token_refresh_scheduler, args=(auth,))
    refresh_thread.daemon = True
    refresh_thread.start()

    return auth
