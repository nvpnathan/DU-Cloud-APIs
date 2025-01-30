import os
import time
import logging
import requests
import threading
from typing import Optional
from dataclasses import dataclass
from urllib.parse import urlparse
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class AuthenticationError(Exception):
    """Base exception for authentication-related errors."""

    pass


class TokenError(AuthenticationError):
    """Raised when there are issues with token operations."""

    pass


class ConfigurationError(AuthenticationError):
    """Raised when there are configuration-related issues."""

    pass


@dataclass
class TokenInfo:
    """Data class to store token information."""

    access_token: str
    expires_in: int
    token_type: str


class Authentication:
    def __init__(self, app_id: str, app_secret: str, auth_url: str):
        """Initialize the Authentication instance with validation."""
        # Initialize lock first, before any other operations
        self._lock = threading.Lock()

        # Now use the lock for the initialization
        with self._lock:
            self._validate_credentials(app_id, app_secret, auth_url)

            self.app_id = app_id
            self.app_secret = app_secret
            self.auth_url = auth_url
            self.bearer_token: Optional[str] = None
            self.token_expiry: Optional[float] = None

        # Get initial token
        try:
            self._initial_token_fetch()
        except AuthenticationError as e:
            logger.error(f"Failed to initialize authentication: {e}")
            raise

    @staticmethod
    def _validate_credentials(app_id: str, app_secret: str, auth_url: str) -> None:
        """Validate the credentials and URL format."""
        if not app_id or not isinstance(app_id, str):
            raise ConfigurationError("Invalid APP_ID: Must be a non-empty string")

        if not app_secret or not isinstance(app_secret, str):
            raise ConfigurationError("Invalid APP_SECRET: Must be a non-empty string")

        try:
            parsed_url = urlparse(auth_url)
            if not (parsed_url.scheme and parsed_url.netloc):
                raise ValueError("Invalid URL format")
        except Exception as e:
            raise ConfigurationError(f"Invalid AUTH_URL: {e}")

    def _initial_token_fetch(self):
        """Fetch initial token without using the lock since we're already in a locked context."""
        try:
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

            response = requests.post(
                self.auth_url,
                data=data,
                timeout=10,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            token_data = response.json()

            # Validate token response
            self._validate_token_response(token_data)

            # Set initial token values
            self.bearer_token = token_data["access_token"]
            self.token_expiry = time.time() + token_data["expires_in"]

        except Exception as e:
            logger.error(f"Failed to fetch initial token: {e}")
            raise TokenError(f"Initial token fetch failed: {str(e)}")

    def get_bearer_token(self) -> str:
        """Get a valid bearer token, refreshing if necessary."""
        # with self._lock:
        if self._is_token_valid():
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
            response = requests.post(
                self.auth_url,
                data=data,
                timeout=30,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            token_data = response.json()

            # Validate token response
            self._validate_token_response(token_data)

            # Update token information
            token_info = TokenInfo(
                access_token=token_data["access_token"],
                expires_in=token_data["expires_in"],
                token_type=token_data["token_type"],
            )

            self._update_token(token_info)
            logger.info("Successfully obtained new bearer token")
            return self.bearer_token

        except requests.exceptions.Timeout:
            raise TokenError("Authentication request timed out")
        except requests.exceptions.ConnectionError:
            raise TokenError("Failed to connect to authentication server")
        except requests.exceptions.HTTPError as e:
            raise TokenError(
                f"HTTP error during authentication: {e.response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            raise TokenError(f"Authentication request failed: {str(e)}")
        except (KeyError, ValueError) as e:
            raise TokenError(f"Invalid token response format: {str(e)}")

    def _validate_token_response(self, token_data: dict) -> None:
        """Validate the token response contains required fields."""
        required_fields = {"access_token", "expires_in", "token_type"}
        missing_fields = required_fields - set(token_data.keys())

        if missing_fields:
            raise TokenError(
                f"Missing required fields in token response: {missing_fields}"
            )

        if not isinstance(token_data["expires_in"], (int, float)):
            raise TokenError("Invalid expires_in value in token response")

    def _update_token(self, token_info: TokenInfo) -> None:
        """Update token information with thread safety."""
        with self._lock:
            self.bearer_token = token_info.access_token
            self.token_expiry = time.time() + token_info.expires_in

    def _is_token_valid(self) -> bool:
        """Check if the current token is valid with a safety margin."""
        EXPIRY_MARGIN = 60  # Seconds before expiry to consider token invalid
        return (
            self.bearer_token is not None
            and self.token_expiry is not None
            and time.time() < (self.token_expiry - EXPIRY_MARGIN)
        )

    def refresh_token(self) -> None:
        """Refresh the bearer token."""
        try:
            self.get_bearer_token()
        except AuthenticationError as e:
            logger.error(f"Failed to refresh token: {e}")
            raise

    def token_validity_duration(self) -> float:
        """Return the remaining validity duration of the token in seconds."""
        if self.token_expiry is None:
            return 0.0
        return max(0.0, self.token_expiry - time.time())


def token_refresh_scheduler(auth_instance: Authentication) -> None:
    """Periodically refresh the bearer token with error handling."""
    while True:
        try:
            # Calculate sleep duration (half of the remaining validity time)
            sleep_duration = max(60, auth_instance.token_validity_duration() / 2)
            time.sleep(sleep_duration)

            auth_instance.refresh_token()
            logger.debug("Token refreshed successfully")

        except AuthenticationError as e:
            logger.error(f"Failed to refresh token in scheduler: {e}")
            # Sleep for a shorter duration on error before retrying
            time.sleep(60)
        except Exception as e:
            logger.error(f"Unexpected error in token refresh scheduler: {e}")
            time.sleep(60)


def initialize_authentication() -> Authentication:
    """Initialize authentication with environment variables."""
    try:
        # Retrieve and validate environment variables
        app_id = os.getenv("APP_ID")
        app_secret = os.getenv("APP_SECRET")
        auth_url = os.getenv("AUTH_URL")

        if not all([app_id, app_secret, auth_url]):
            raise ConfigurationError(
                "Missing required environment variables. "
                "Please ensure APP_ID, APP_SECRET, and AUTH_URL are set."
            )

        # Initialize Authentication
        auth = Authentication(app_id, app_secret, auth_url)

        # Create and start token refresh thread
        refresh_thread = threading.Thread(
            target=token_refresh_scheduler,
            args=(auth,),
            daemon=True,
            name="TokenRefreshThread",
        )
        refresh_thread.start()
        logger.info("Authentication initialized successfully")

        return auth

    except Exception as e:
        logger.error(f"Failed to initialize authentication: {e}")
        raise
