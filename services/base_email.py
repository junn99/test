"""Base email service interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class EmailMessage:
    """Standardized email message structure."""

    id: str
    thread_id: str
    subject: str
    sender: str
    recipients: List[str]
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    body: str
    html_body: Optional[str] = None
    date: datetime
    is_read: bool = False
    is_starred: bool = False
    labels: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "subject": self.subject,
            "sender": self.sender,
            "recipients": self.recipients,
            "cc": self.cc,
            "bcc": self.bcc,
            "body": self.body,
            "html_body": self.html_body,
            "date": self.date.isoformat(),
            "is_read": self.is_read,
            "is_starred": self.is_starred,
            "labels": self.labels,
            "attachments": self.attachments,
            "snippet": self.snippet,
        }


@dataclass
class EmailDraft:
    """Email draft structure."""

    to: List[str]
    subject: str
    body: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    html_body: Optional[str] = None
    attachments: Optional[List[str]] = None


class BaseEmailService(ABC):
    """Abstract base class for email services."""

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the email service.

        Returns:
            True if authentication successful
        """
        pass

    @abstractmethod
    def get_messages(
        self,
        max_results: int = 10,
        query: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
        unread_only: bool = False
    ) -> List[EmailMessage]:
        """Fetch email messages.

        Args:
            max_results: Maximum number of messages to retrieve
            query: Search query string
            label_ids: List of label IDs to filter by
            unread_only: Only fetch unread messages

        Returns:
            List of EmailMessage objects
        """
        pass

    @abstractmethod
    def get_message_by_id(self, message_id: str) -> Optional[EmailMessage]:
        """Get a specific message by ID.

        Args:
            message_id: The message ID

        Returns:
            EmailMessage object or None
        """
        pass

    @abstractmethod
    def send_message(self, draft: EmailDraft) -> bool:
        """Send an email message.

        Args:
            draft: EmailDraft object containing message details

        Returns:
            True if sent successfully
        """
        pass

    @abstractmethod
    def create_draft(self, draft: EmailDraft) -> Optional[str]:
        """Create an email draft.

        Args:
            draft: EmailDraft object

        Returns:
            Draft ID if created successfully, None otherwise
        """
        pass

    @abstractmethod
    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read.

        Args:
            message_id: The message ID

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def mark_as_unread(self, message_id: str) -> bool:
        """Mark a message as unread.

        Args:
            message_id: The message ID

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def delete_message(self, message_id: str) -> bool:
        """Delete a message.

        Args:
            message_id: The message ID

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def search_messages(
        self,
        query: str,
        max_results: int = 10
    ) -> List[EmailMessage]:
        """Search for messages matching a query.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            List of matching EmailMessage objects
        """
        pass
