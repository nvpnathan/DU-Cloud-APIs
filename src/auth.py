import time
import requests


class Authentication:
    def __init__(self, client_id, client_secret, token_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token = None
        self.token_expiry = None

    def get_bearer_token(self) -> str | None:
        # Check if token is already obtained and not expired
        if self.access_token and self.token_expiry and time.time() < self.token_expiry:
            return self.access_token

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
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
            response = requests.post(self.token_url, data=data, timeout=30)
            response.raise_for_status()  # Raise an exception for HTTP errors

            token_data = response.json()

            # Extract and store the access token and its expiry time
            self.access_token = token_data.get("access_token")
            self.token_expiry = time.time() + token_data.get("expires_in", 3600)

            if self.access_token:
                print("Authenticated!\n")
                return self.access_token
            else:
                print("Error: No access token received")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching token: {e}")
            return None

    def refresh_token(self):
        # Call get_bearer_token to refresh the token
        self.get_bearer_token()

    def token_validity_duration(self):
        # Return the remaining validity duration of the token
        if self.token_expiry:
            return max(0, self.token_expiry - time.time())
        else:
            return 0
