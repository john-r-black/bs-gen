import os
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Allow OAuth over HTTP (Cloud Run terminates HTTPS, so internal traffic is HTTP)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Relax token scope validation (Google returns scopes in different order)
# See: https://stackoverflow.com/questions/51499034/google-oauthlib-scope-has-changed
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

# OAuth2 configuration
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/drive'
]


def get_oauth_flow(request: Request) -> Flow:
    """Create OAuth flow instance"""
    client_config = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [f"{os.getenv('APP_URL')}/auth/callback"]
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=f"{os.getenv('APP_URL')}/auth/callback"
    )

    return flow


async def oauth_login(request: Request):
    """Initiate Google OAuth login flow"""
    flow = get_oauth_flow(request)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )

    # Store state in session
    request.session["oauth_state"] = state

    return RedirectResponse(url=authorization_url)


async def oauth_callback(request: Request):
    """Handle OAuth callback from Google"""
    # Verify state
    state = request.session.get("oauth_state")
    if not state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    # Exchange authorization code for credentials
    flow = get_oauth_flow(request)

    # Fetch token - OAUTHLIB_RELAX_TOKEN_SCOPE handles scope reordering automatically
    flow.fetch_token(authorization_response=str(request.url))

    # Get credentials from flow (now works properly with relaxed scope validation)
    credentials = flow.credentials

    # Get user info
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()

    # Verify user email
    allowed_email = os.getenv("ALLOWED_EMAIL")
    if user_info.get("email") != allowed_email:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Only {allowed_email} is authorized."
        )

    # Store credentials and user info in session
    request.session["credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }
    request.session["user"] = {
        "email": user_info.get("email"),
        "name": user_info.get("name"),
        "picture": user_info.get("picture")
    }

    return RedirectResponse(url="/")


async def logout(request: Request):
    """Logout user and clear session"""
    request.session.clear()
    return RedirectResponse(url="/login")


async def get_current_user(request: Request):
    """Get current authenticated user from session"""
    return request.session.get("user")


def get_credentials(request: Request) -> Credentials:
    """Get Google credentials from session"""
    creds_data = request.session.get("credentials")
    if not creds_data:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return Credentials(
        token=creds_data["token"],
        refresh_token=creds_data.get("refresh_token"),
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=creds_data["scopes"]
    )
