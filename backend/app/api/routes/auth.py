# backend/app/api/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from typing import Any

from ...config import settings
from ...integrations.google_auth import (
    build_oauth_client, 
    exchange_code_for_token, 
    store_credentials_to_file,
    get_authorized_http # Keep this import for the status check
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
        # Using status code 503 (Service Unavailable) might be more appropriate if configuration failed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service initialization failed. Check server logs for details."
        )


@router.get("/login", summary="Initiate Google OAuth Login Flow")
async def google_login(flow: Any = Depends(get_oauth_flow)):
    """
    Redirects the user to Google's authorization page.
    """
    # Using the 127.0.0.1 redirect URL for consistency with Uvicorn host
    authorization_url, state = flow.authorization_url(
        access_type='offline',          # Ensures a Refresh Token is returned
        include_granted_scopes='true',  # Re-prompts only for new scopes
        prompt='consent'                # Forces consent screen every time for testing
    )
    
    logger.info("Redirecting user to Google for authorization.")
    return RedirectResponse(url=authorization_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/callback", summary="Google OAuth Callback")
async def google_callback(
    code: str, 
    state: str, 
    flow: Any = Depends(get_oauth_flow)
):
    """
    Receives the authorization code and exchanges it for a token (credentials).
    """
    try:
        # 1. Exchange the authorization code for credentials
        credentials = exchange_code_for_token(code, flow)
        
        # 2. Store the credentials (token.json)
        store_credentials_to_file(credentials, settings.TOKEN_PATH)
        
        # CRUCIAL FIX: Removed the premature call to get_authorized_http(credentials) here. 
        # The credentials are saved and will be loaded later when an API call is made.
        
        logger.info(f"Successfully obtained and stored credentials at {settings.TOKEN_PATH}")
        
        # 3. Redirect back to the frontend on success
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/success", 
            status_code=status.HTTP_302_FOUND
        )

    except Exception as e:
        # Catch and log specific errors for better debugging
        if "Scope has changed" in str(e):
             logger.error(f"Google OAuth callback failed due to scope mismatch: {e}")
             detail_message = "Scope_Mismatch"
        else:
             logger.error(f"Google OAuth callback failed: {e}")
             detail_message = "Authorization_Failed"

        # Redirect back to the frontend with an error status
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/error?message={detail_message}", 
            status_code=status.HTTP_302_FOUND
        )


@router.get("/status", summary="Check Authentication Status")
async def auth_status():
    """
    Checks if the token.json file exists and attempts to validate it by refreshing/loading.
    """
    token_path = settings.TOKEN_PATH
    if token_path.exists():
        # Attempt to load and refresh credentials to ensure they are still good
        try:
            # Calling get_authorized_http() here will load the token, 
            # refresh it if expired, and raise an exception if it fails.
            # We don't need the return value, just the side effect of validation/refresh.
            get_authorized_http() 
            return {
                "status": "authenticated", 
                "message": "Token file found and is valid. Ready to use Google APIs."
            }
        except PermissionError as e:
            # This is the expected error if the refresh fails or the token is bad/missing.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error checking token status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error validating authentication token."
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token file not found. User must login via /auth/login."
        )