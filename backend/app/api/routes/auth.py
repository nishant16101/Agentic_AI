# backend/app/api/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from typing import Any

from ...config import settings
from ...integrations.google_auth import (
    build_oauth_client, 
    exchange_code_for_token, 
    store_credentials_to_file,
    get_authorized_http
)
from ...utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Dependency to ensure the Google OAuth client is available
def get_oauth_flow():
    """Initializes and returns the Google OAuth flow client."""
    try:
        flow = build_oauth_client()
        return flow
    except Exception as e:
        logger.error(f"Failed to build Google OAuth flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service initialization failed."
        )



@router.get("/login", summary="Initiate Google OAuth Login Flow")
async def google_login(flow: Any = Depends(get_oauth_flow)):
    """
    Redirects the user to Google's authorization page.
    """
    # The 'state' is a security measure to prevent CSRF attacks
    authorization_url, state = flow.authorization_url(
        access_type='offline',          # Ensures a Refresh Token is returned
        include_granted_scopes='true'   # Includes previously granted scopes
    )
    
    # In a real app, you would store the 'state' in a user session/cookie
    # for verification in the /callback endpoint. For this simple agent setup,
    # we just need the URL.
    logger.info("Redirecting user to Google for authorization.")
    return RedirectResponse(authorization_url)


@router.get("/callback", summary="Google OAuth Callback Endpoint")
async def google_callback(
    code: str, 
    # state: str, # Uncomment and use if you implemented full CSRF protection
    flow: Any = Depends(get_oauth_flow)
):
    """
    Exchanges the authorization code for access and refresh tokens, 
    and saves them to token.json.
    """
    try:
        # 1. Exchange the authorization code for credentials
        credentials = exchange_code_for_token(code, flow)
        
        # 2. Store the credentials (token.json)
        store_credentials_to_file(credentials, settings.TOKEN_PATH)
        
        
        get_authorized_http(credentials) 

        logger.info(f"Successfully obtained and stored credentials at {settings.TOKEN_PATH}")
        
        # 3. Redirect back to the frontend on success
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/success", 
            status_code=status.HTTP_302_FOUND
        )

    except Exception as e:
        logger.error(f"Google OAuth callback failed: {e}")
        # Redirect back to the frontend with an error status
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/error?message=Authorization_Failed", 
            status_code=status.HTTP_302_FOUND
        )



@router.get("/status", summary="Check Authentication Status")
async def auth_status():
    """
    Checks if the token.json file exists and is potentially valid.
    """
    token_path = settings.TOKEN_PATH
    if token_path.exists():
        return {
            "status": "authenticated", 
            "message": "Token file found. Ready to use Google APIs."
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. token.json file not found."
        )