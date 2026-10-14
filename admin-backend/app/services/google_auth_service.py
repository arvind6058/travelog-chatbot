from typing import Dict, Any, Optional
import httpx
import logging
from urllib.parse import urlencode
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("travelogix.auth.google")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


class GoogleAuthService:
    @staticmethod
    def is_configured() -> bool:
        """
        Returns True if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set to real values (not placeholders).
        """
        client_id = settings.GOOGLE_CLIENT_ID.strip()
        client_secret = settings.GOOGLE_CLIENT_SECRET.strip()
        
        if not client_id or not client_secret:
            return False
            
        invalid_keywords = ["your_google", "your_client", "sampleclientid", "sample_client", "123456789012", "placeholder", "dummy", "xxxx"]
        if any(kw in client_id.lower() for kw in invalid_keywords) or any(kw in client_secret.lower() for kw in invalid_keywords):
            return False
            
        return True

    @staticmethod
    def get_masked_client_id() -> str:
        client_id = settings.GOOGLE_CLIENT_ID.strip()
        if not GoogleAuthService.is_configured():
            return "NOT CONFIGURED / PLACEHOLDER"
        if len(client_id) > 12:
            return f"{client_id[:6]}...{client_id[-20:]}"
        return client_id

    @staticmethod
    def log_diagnostics():
        """
        Safe diagnostic logging that never exposes secrets.
        """
        configured = GoogleAuthService.is_configured()
        masked_id = GoogleAuthService.get_masked_client_id()
        secret_set = bool(settings.GOOGLE_CLIENT_SECRET.strip()) and configured

        logger.info(
            "Google OAuth configuration | client_id=%s (%s) | client_secret=%s | redirect_uri=%s",
            "configured" if configured else "missing",
            masked_id,
            "configured" if secret_set else "missing",
            settings.GOOGLE_REDIRECT_URI,
        )

    @staticmethod
    def get_authorization_url(state: str) -> str:
        """
        Build official Google OAuth 2.0 Authorization URL using verified client_id.
        Raises ValueError if client_id is not configured, preventing sending invalid placeholders to Google.
        """
        if not GoogleAuthService.is_configured():
            raise ValueError(
                "Google OAuth client ID is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env with your Google Cloud Web Client ID."
            )

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID.strip(),
            "redirect_uri": settings.GOOGLE_REDIRECT_URI.strip(),
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    @staticmethod
    async def exchange_code_and_get_user_info(code: str) -> Dict[str, Any]:
        """
        Exchange OAuth authorization code for Google access token and retrieve verified user identity.
        """
        if not GoogleAuthService.is_configured():
            raise ValueError(
                "Google OAuth credentials (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET) are not configured in backend/.env file."
            )

        token_payload = {
            "client_id": settings.GOOGLE_CLIENT_ID.strip(),
            "client_secret": settings.GOOGLE_CLIENT_SECRET.strip(),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI.strip(),
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Exchange authorization code for tokens
            token_res = await client.post(GOOGLE_TOKEN_URL, data=token_payload)
            if token_res.status_code != 200:
                error_detail = token_res.text
                raise ValueError(f"Google token exchange failed: {error_detail}")

            token_data = token_res.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError("No access_token returned from Google OAuth service.")

            # 2. Fetch verified Google user profile
            user_res = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if user_res.status_code != 200:
                raise ValueError("Failed to retrieve Google user profile information.")

            user_info = user_res.json()
            email = user_info.get("email")
            if not email:
                raise ValueError("Google user profile did not provide a verified email address.")

            return {
                "email": email,
                "email_verified": user_info.get("email_verified"),
                "name": user_info.get("name") or email.split("@")[0],
                "google_id": user_info.get("sub"),
                "picture": user_info.get("picture"),
            }
