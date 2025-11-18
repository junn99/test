"""Gmail service implementation."""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger
import html2text

from services.base_email import BaseEmailService, EmailMessage, EmailDraft
from utils.auth import GmailAuthenticator


class GmailService(BaseEmailService):
    """Gmail API service implementation."""

    def __init__(self, authenticator: Optional[GmailAuthenticator] = None):
        """Initialize Gmail service.

        Args:
            authenticator: GmailAuthenticator instance
        """
        self.authenticator = authenticator or GmailAuthenticator()
        self.service = None
        self.user_id = "me"

    def authenticate(self) -> bool:
        """Authenticate with Gmail API.

        Returns:
            True if authentication successful
        """
        try:
            creds = self.authenticator.get_credentials()
            self.service = build("gmail", "v1", credentials=creds)
            logger.info("Gmail service authenticated successfully")
            return True
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            return False

    def _parse_message(self, message_data: dict) -> EmailMessage:
        """Parse Gmail API message to EmailMessage object.

        Args:
            message_data: Raw message data from Gmail API

        Returns:
            EmailMessage object
        """
        headers = {
            header["name"]: header["value"]
            for header in message_data["payload"].get("headers", [])
        }

        # Extract body
        body = ""
        html_body = None

        if "parts" in message_data["payload"]:
            for part in message_data["payload"]["parts"]:
                if part["mimeType"] == "text/plain":
                    if "data" in part["body"]:
                        body = base64.urlsafe_b64decode(
                            part["body"]["data"]
                        ).decode("utf-8")
                elif part["mimeType"] == "text/html":
                    if "data" in part["body"]:
                        html_body = base64.urlsafe_b64decode(
                            part["body"]["data"]
                        ).decode("utf-8")
        else:
            # Simple message without parts
            if "data" in message_data["payload"].get("body", {}):
                body_data = message_data["payload"]["body"]["data"]
                body = base64.urlsafe_b64decode(body_data).decode("utf-8")

        # If only HTML body available, convert to text
        if not body and html_body:
            h = html2text.HTML2Text()
            h.ignore_links = False
            body = h.handle(html_body)

        # Parse date
        date_str = headers.get("Date", "")
        try:
            from email.utils import parsedate_to_datetime
            date = parsedate_to_datetime(date_str)
        except Exception:
            date = datetime.now()

        # Check if read
        label_ids = message_data.get("labelIds", [])
        is_read = "UNREAD" not in label_ids
        is_starred = "STARRED" in label_ids

        return EmailMessage(
            id=message_data["id"],
            thread_id=message_data.get("threadId", ""),
            subject=headers.get("Subject", "(No Subject)"),
            sender=headers.get("From", ""),
            recipients=headers.get("To", "").split(","),
            cc=headers.get("Cc", "").split(",") if headers.get("Cc") else None,
            body=body,
            html_body=html_body,
            date=date,
            is_read=is_read,
            is_starred=is_starred,
            labels=label_ids,
            snippet=message_data.get("snippet", ""),
        )

    def get_messages(
        self,
        max_results: int = 10,
        query: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
        unread_only: bool = False
    ) -> List[EmailMessage]:
        """Fetch email messages from Gmail.

        Args:
            max_results: Maximum number of messages
            query: Gmail search query
            label_ids: List of label IDs
            unread_only: Only fetch unread messages

        Returns:
            List of EmailMessage objects
        """
        if not self.service:
            self.authenticate()

        try:
            # Build query
            search_query = query or ""
            if unread_only:
                search_query = f"{search_query} is:unread".strip()

            # Fetch message list
            results = self.service.users().messages().list(
                userId=self.user_id,
                maxResults=max_results,
                q=search_query,
                labelIds=label_ids
            ).execute()

            messages = results.get("messages", [])
            email_messages = []

            # Fetch full message details
            for msg in messages:
                try:
                    message_data = self.service.users().messages().get(
                        userId=self.user_id,
                        id=msg["id"],
                        format="full"
                    ).execute()
                    email_messages.append(self._parse_message(message_data))
                except HttpError as e:
                    logger.error(f"Error fetching message {msg['id']}: {e}")
                    continue

            logger.info(f"Fetched {len(email_messages)} messages")
            return email_messages

        except HttpError as e:
            logger.error(f"Error fetching messages: {e}")
            return []

    def get_message_by_id(self, message_id: str) -> Optional[EmailMessage]:
        """Get a specific message by ID.

        Args:
            message_id: Gmail message ID

        Returns:
            EmailMessage object or None
        """
        if not self.service:
            self.authenticate()

        try:
            message_data = self.service.users().messages().get(
                userId=self.user_id,
                id=message_id,
                format="full"
            ).execute()
            return self._parse_message(message_data)
        except HttpError as e:
            logger.error(f"Error fetching message {message_id}: {e}")
            return None

    def _create_message(self, draft: EmailDraft) -> dict:
        """Create a MIME message from EmailDraft.

        Args:
            draft: EmailDraft object

        Returns:
            Dictionary with base64 encoded message
        """
        if draft.html_body:
            message = MIMEMultipart("alternative")
            part1 = MIMEText(draft.body, "plain")
            part2 = MIMEText(draft.html_body, "html")
            message.attach(part1)
            message.attach(part2)
        else:
            message = MIMEText(draft.body)

        message["to"] = ", ".join(draft.to)
        message["subject"] = draft.subject

        if draft.cc:
            message["cc"] = ", ".join(draft.cc)
        if draft.bcc:
            message["bcc"] = ", ".join(draft.bcc)

        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("utf-8")

        return {"raw": raw_message}

    def send_message(self, draft: EmailDraft) -> bool:
        """Send an email message via Gmail.

        Args:
            draft: EmailDraft object

        Returns:
            True if sent successfully
        """
        if not self.service:
            self.authenticate()

        try:
            message = self._create_message(draft)
            sent_message = self.service.users().messages().send(
                userId=self.user_id,
                body=message
            ).execute()
            logger.info(f"Message sent successfully. ID: {sent_message['id']}")
            return True
        except HttpError as e:
            logger.error(f"Error sending message: {e}")
            return False

    def create_draft(self, draft: EmailDraft) -> Optional[str]:
        """Create an email draft in Gmail.

        Args:
            draft: EmailDraft object

        Returns:
            Draft ID if successful
        """
        if not self.service:
            self.authenticate()

        try:
            message = self._create_message(draft)
            draft_body = {"message": message}
            created_draft = self.service.users().drafts().create(
                userId=self.user_id,
                body=draft_body
            ).execute()
            draft_id = created_draft["id"]
            logger.info(f"Draft created successfully. ID: {draft_id}")
            return draft_id
        except HttpError as e:
            logger.error(f"Error creating draft: {e}")
            return None

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a Gmail message as read.

        Args:
            message_id: Gmail message ID

        Returns:
            True if successful
        """
        if not self.service:
            self.authenticate()

        try:
            self.service.users().messages().modify(
                userId=self.user_id,
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            logger.info(f"Message {message_id} marked as read")
            return True
        except HttpError as e:
            logger.error(f"Error marking message as read: {e}")
            return False

    def mark_as_unread(self, message_id: str) -> bool:
        """Mark a Gmail message as unread.

        Args:
            message_id: Gmail message ID

        Returns:
            True if successful
        """
        if not self.service:
            self.authenticate()

        try:
            self.service.users().messages().modify(
                userId=self.user_id,
                id=message_id,
                body={"addLabelIds": ["UNREAD"]}
            ).execute()
            logger.info(f"Message {message_id} marked as unread")
            return True
        except HttpError as e:
            logger.error(f"Error marking message as unread: {e}")
            return False

    def delete_message(self, message_id: str) -> bool:
        """Delete a Gmail message.

        Args:
            message_id: Gmail message ID

        Returns:
            True if successful
        """
        if not self.service:
            self.authenticate()

        try:
            self.service.users().messages().trash(
                userId=self.user_id,
                id=message_id
            ).execute()
            logger.info(f"Message {message_id} moved to trash")
            return True
        except HttpError as e:
            logger.error(f"Error deleting message: {e}")
            return False

    def search_messages(
        self,
        query: str,
        max_results: int = 10
    ) -> List[EmailMessage]:
        """Search for messages in Gmail.

        Args:
            query: Gmail search query
            max_results: Maximum results

        Returns:
            List of EmailMessage objects
        """
        return self.get_messages(
            max_results=max_results,
            query=query
        )
