import json
from google_auth_oathlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp

from ..config import settings
from ..utils.logger import get_logger
logger = get_logger(__name__)


#google auth library needs this in json format
CLIENT_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        "scope": settings.GOOGLE_SCOPES
        
}

}

def get_google_flow() ->Flow:
    """Intialzes the Google OAuth Flow object."""
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes = settings.GOOGLE_SCOPES,
        redirect_uri = settings.GOOGLE_REDIRECT_URI
    )
    return flow


def load_credentials()->Credentials | None:
    """Loads stored user credentials from token.json"""
    if settings.TOKEN_PATH.exists():
        try:
            with open(settings.TOKEN_PATH,"r") as token:
                creds = Credentials.from_authorized_user_file(settings.TOKEN_PATH)
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired Google token")
                    creds.refresh(Request())
                    save_credentials(creds)
                return creds
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            settings.TOKEN_PATH.unlink(missing_ok=True)
        return None
    return None

def save_credentials(creds:Credentials):
    settings.CREDENTIALS_DIR.mkdir(exist_ok=True)
    with open(settings.TOKEN_PATH,"w") as token:
        token.write(creds.to_json())
    logger.info("Google credentials saved successfully.")

def get_authorized_http(creds:Credentials)->AuthorizedHttp:
    creds = load_credentials()
    if not creds:
        raise Exception("No valid Google credentials found.")
    return AuthorizedHttp(creds)