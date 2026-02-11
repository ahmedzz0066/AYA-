"""Microsoft OAuth2 authentication using MSAL."""

import json
import os

import msal

from app.config import Config

TOKEN_CACHE_FILE = "token_cache.json"


def _load_cache():
    """Load the MSAL token cache from disk."""
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_FILE):
        with open(TOKEN_CACHE_FILE, "r") as f:
            cache.deserialize(f.read())
    return cache


def _save_cache(cache):
    """Persist the MSAL token cache to disk."""
    if cache.has_state_changed:
        with open(TOKEN_CACHE_FILE, "w") as f:
            f.write(cache.serialize())


def _build_msal_app(cache=None):
    """Create a confidential client application."""
    return msal.ConfidentialClientApplication(
        client_id=Config.MS_CLIENT_ID,
        client_credential=Config.MS_CLIENT_SECRET,
        authority=Config.MS_AUTHORITY,
        token_cache=cache,
    )


def get_auth_url():
    """Generate the Microsoft login URL for the user."""
    app = _build_msal_app()
    return app.get_authorization_request_url(
        scopes=Config.MS_SCOPES,
        redirect_uri=Config.MS_REDIRECT_URI,
    )


def acquire_token_by_code(auth_code):
    """Exchange the authorization code for an access token."""
    cache = _load_cache()
    app = _build_msal_app(cache=cache)
    result = app.acquire_token_by_authorization_code(
        code=auth_code,
        scopes=Config.MS_SCOPES,
        redirect_uri=Config.MS_REDIRECT_URI,
    )
    _save_cache(cache)
    return result


def get_token_silent():
    """Try to get a cached/refreshed token without user interaction."""
    cache = _load_cache()
    app = _build_msal_app(cache=cache)
    accounts = app.get_accounts()
    if not accounts:
        return None
    result = app.acquire_token_silent(
        scopes=Config.MS_SCOPES,
        account=accounts[0],
    )
    _save_cache(cache)
    return result


def is_authenticated():
    """Check if we have a valid token."""
    token = get_token_silent()
    return token is not None and "access_token" in token


def get_access_token():
    """Get a valid access token, or None if not authenticated."""
    token = get_token_silent()
    if token and "access_token" in token:
        return token["access_token"]
    return None


def logout():
    """Clear the token cache."""
    if os.path.exists(TOKEN_CACHE_FILE):
        os.remove(TOKEN_CACHE_FILE)
