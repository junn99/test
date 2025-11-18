"""Authentication utilities for email services."""

import os
import pickle
from typing import Optional
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from loguru import logger

from config.settings import settings


class GmailAuthenticator:
    """Handle Gmail OAuth2 authentication."""

    def __init__(
        self,
        credentials_file: Optional[str] = None,
        token_file: Optional[str] = None,
        scopes: Optional[list[str]] = None
    ):
        """Initialize Gmail authenticator.

        Args:
            credentials_file: Path to OAuth2 credentials JSON file
            token_file: Path to store/load access token
            scopes: List of Gmail API scopes
        """
        self.credentials_file = credentials_file or settings.gmail_credentials_file
        self.token_file = token_file or settings.gmail_token_file
        self.scopes = scopes or settings.gmail_scopes
        self.creds: Optional[Credentials] = None

    def authenticate(self) -> Credentials:
        """Authenticate with Gmail API using OAuth2.

        Returns:
            Google OAuth2 Credentials object

        Raises:
            FileNotFoundError: If credentials file not found
            Exception: If authentication fails
        """
        # Check if token file exists and load credentials
        if os.path.exists(self.token_file):
            logger.info(f"Loading credentials from {self.token_file}")
            with open(self.token_file, "rb") as token:
                self.creds = pickle.load(token)

        # If credentials don't exist or are invalid, refresh or authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                logger.info("Refreshing expired credentials")
                self.creds.refresh(Request())
            else:
                # Perform OAuth2 flow
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        "Please download credentials.json from Google Cloud Console:\n"
                        "https://console.cloud.google.com/apis/credentials"
                    )

                logger.info("Starting OAuth2 authentication flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes
                )
                self.creds = flow.run_local_server(port=0)

            # Save credentials for next run
            logger.info(f"Saving credentials to {self.token_file}")
            with open(self.token_file, "wb") as token:
                pickle.dump(self.creds, token)

        return self.creds

    def get_credentials(self) -> Credentials:
        """Get valid credentials, authenticating if necessary.

        Returns:
            Valid Google OAuth2 Credentials
        """
        if not self.creds or not self.creds.valid:
            return self.authenticate()
        return self.creds

    def revoke_credentials(self) -> None:
        """Revoke current credentials and delete token file."""
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            logger.info("Credentials revoked and token file deleted")
        self.creds = None


class OutlookAuthenticator:
    """Handle Microsoft Outlook OAuth2 authentication.

    Note: This is a placeholder for future Outlook support.
    """

    def __init__(self):
        """Initialize Outlook authenticator."""
        self.client_id = settings.outlook_client_id
        self.client_secret = settings.outlook_client_secret
        self.tenant_id = settings.outlook_tenant_id

    def authenticate(self):
        """Authenticate with Outlook API.

        TODO: Implement Outlook OAuth2 flow using MSAL
        """
        raise NotImplementedError("Outlook authentication not yet implemented")
