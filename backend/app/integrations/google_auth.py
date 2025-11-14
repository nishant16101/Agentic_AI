import os
import json
import httplib2
from typing import Any, Optional
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth import default as google_auth_default

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

# --- Configuration Constants ---
# The file that contains the downloaded Client ID and Secret (downloaded from GCP)
CREDENTIALS_FILE = settings.CREDENTIALS_DIR / "credentials.json"


def build_oauth_client() -> Flow:
    """
    Initializes and returns the Google OAuth flow object.
    
    This function prioritizes reading credentials from Pydantic settings 
    (which reads from .env) and builds the necessary client configuration 
    for the OAuth flow.
    """
    
    # 1. Use a dictionary structure that mimics the credentials.json content
    #    but pull the critical pieces from settings (loaded from .env).
    try:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in the .env file.")
            
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "javascript_origins": [settings.FRONTEND_URL],
            }
        }

        # 2. Build the flow object
        flow = Flow.from_client_config(
            client_config=client_config,
            scopes=settings.GOOGLE_SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        return flow
    
    except ValueError as e:
        logger.error(f"Failed to build Google OAuth flow due to missing environment variables: {e}")
        # Reraise as a custom error that can be caught by the router
        raise RuntimeError("Google OAuth configuration missing. Check your .env file.")
    
    except Exception as e:
        logger.error(f"Unexpected error during OAuth client build: {e}")
        raise RuntimeError(f"Failed to initialize Google OAuth flow: {e}")


def load_credentials_from_file(token_path: Path) -> Optional[Credentials]:
    """Loads credentials from the specified JSON file."""
    if not token_path.exists():
        return None
    try:
        with open(token_path, 'r') as token_file:
            # We use json.load to read the token file created by the flow, not the client config
            creds_data = json.load(token_file)
            return Credentials.from_authorized_user_info(info=creds_data, scopes=settings.GOOGLE_SCOPES)
    except Exception as e:
        logger.error(f"Error loading credentials from token.json: {e}")
        return None

def store_credentials_to_file(credentials: Credentials, token_path: Path):
    """Saves the credentials (including refresh token) to the specified file."""
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, 'w') as token_file:
        token_file.write(credentials.to_json())

def exchange_code_for_token(code: str, flow: Flow) -> Credentials:
    """Exchanges the authorization code for an OAuth token."""
    flow.fetch_token(code=code)
    return flow.credentials


def get_authorized_http(credentials: Optional[Credentials] = None) -> httplib2.Http:
    """
    Retrieves or loads the Google credentials, ensures they are valid/refreshed,
    and returns an authorized httplib2.Http object for API calls.
    """
    if not credentials:
        credentials = load_credentials_from_file(settings.TOKEN_PATH)
    
    if not credentials:
        logger.error("Authentication required: token.json not found or invalid.")
        raise PermissionError("Authentication required. Please run the OAuth flow via the /auth/login endpoint.")
    
    # Check if credentials need refreshing
    if credentials.expired and credentials.refresh_token:
        try:
            # Use the refresh token to get a new access token
            credentials.refresh(Request())
            # Save the refreshed credentials back to the file
            store_credentials_to_file(credentials, settings.TOKEN_PATH)
            logger.info("Successfully refreshed Google access token.")
        except Exception as e:
            # If refresh fails (e.g., revoked token), log and force re-auth
            logger.error(f"Failed to refresh token. User must re-authenticate. Error: {e}")
            # Ensure file is removed if refresh fails to force re-authentication
            if settings.TOKEN_PATH.exists():
                os.remove(settings.TOKEN_PATH)
            raise PermissionError("Token refresh failed. User must re-authenticate.")
            
    # Return the authorized HTTP object used by googleapiclient.discovery.build
    return credentials.authorize(httplib2.Http())