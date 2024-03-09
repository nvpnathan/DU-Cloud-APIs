import requests


class Authentication:
    def __init__(self, client_id, client_secret, token_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url

    def get_bearer_token(self) -> (str | None):
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'scope': (
                'Du.DocumentManager.Document '
                'Du.Classification.Api '
                'Du.Digitization.Api '
                'Du.Extraction.Api '
                'Du.Validation.Api'
            )
        }

        try:
            # Make the POST request to obtain the token
            response = requests.post(self.token_url, data=data, timeout=30)
            response.raise_for_status()  # Raise an exception for HTTP errors

            token_data = response.json()

            # Extract and return the access token
            access_token = token_data.get('access_token')
            if access_token:
                print("Authenticated!\n")
                return access_token
            else:
                print("Error: No access token received")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching token: {e}")
            return None
