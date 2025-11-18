"""LangChain tools for email operations."""

from typing import Optional, List
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from loguru import logger

from services.base_email import EmailDraft
from services.gmail_service import GmailService


class GetEmailsInput(BaseModel):
    """Input schema for get_emails tool."""

    max_results: int = Field(default=10, description="Maximum number of emails to fetch")
    query: Optional[str] = Field(default=None, description="Search query (e.g., 'from:example@gmail.com')")
    unread_only: bool = Field(default=False, description="Only fetch unread emails")


class GetEmailsTool(BaseTool):
    """Tool to fetch emails from inbox."""

    name: str = "get_emails"
    description: str = """
    Fetch emails from the inbox. Use this to check new emails, search for specific emails, or list recent messages.
    You can specify search queries like 'from:email@example.com', 'subject:meeting', 'is:unread', etc.
    """
    args_schema: type[BaseModel] = GetEmailsInput
    email_service: GmailService = Field(default_factory=GmailService)

    class Config:
        arbitrary_types_allowed = True

    def _run(
        self,
        max_results: int = 10,
        query: Optional[str] = None,
        unread_only: bool = False
    ) -> str:
        """Fetch emails and return summary."""
        try:
            messages = self.email_service.get_messages(
                max_results=max_results,
                query=query,
                unread_only=unread_only
            )

            if not messages:
                return "No emails found matching the criteria."

            result = f"Found {len(messages)} email(s):\n\n"
            for i, msg in enumerate(messages, 1):
                result += f"{i}. [{msg.id}]\n"
                result += f"   From: {msg.sender}\n"
                result += f"   Subject: {msg.subject}\n"
                result += f"   Date: {msg.date}\n"
                result += f"   Read: {msg.is_read}\n"
                result += f"   Preview: {msg.snippet[:100]}...\n\n"

            return result
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return f"Error fetching emails: {str(e)}"


class ReadEmailInput(BaseModel):
    """Input schema for read_email tool."""

    message_id: str = Field(description="The ID of the email message to read")


class ReadEmailTool(BaseTool):
    """Tool to read a specific email."""

    name: str = "read_email"
    description: str = "Read the full content of a specific email by its ID."
    args_schema: type[BaseModel] = ReadEmailInput
    email_service: GmailService = Field(default_factory=GmailService)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, message_id: str) -> str:
        """Read email content."""
        try:
            message = self.email_service.get_message_by_id(message_id)

            if not message:
                return f"Email with ID {message_id} not found."

            result = f"Email ID: {message.id}\n"
            result += f"Subject: {message.subject}\n"
            result += f"From: {message.sender}\n"
            result += f"To: {', '.join(message.recipients)}\n"
            result += f"Date: {message.date}\n"
            result += f"\nBody:\n{message.body}\n"

            return result
        except Exception as e:
            logger.error(f"Error reading email: {e}")
            return f"Error reading email: {str(e)}"


class ComposeEmailInput(BaseModel):
    """Input schema for compose_email tool."""

    to: List[str] = Field(description="List of recipient email addresses")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body content")
    cc: Optional[List[str]] = Field(default=None, description="CC recipients")


class ComposeEmailTool(BaseTool):
    """Tool to compose and save email draft."""

    name: str = "compose_email"
    description: str = """
    Compose a new email and save it as a draft. Use this to create email drafts that can be reviewed before sending.
    """
    args_schema: type[BaseModel] = ComposeEmailInput
    email_service: GmailService = Field(default_factory=GmailService)

    class Config:
        arbitrary_types_allowed = True

    def _run(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None
    ) -> str:
        """Create email draft."""
        try:
            draft = EmailDraft(
                to=to,
                subject=subject,
                body=body,
                cc=cc
            )

            draft_id = self.email_service.create_draft(draft)

            if draft_id:
                return f"Draft created successfully! Draft ID: {draft_id}\n\nTo: {', '.join(to)}\nSubject: {subject}\n\nUse send_email tool to send this draft."
            else:
                return "Failed to create draft."

        except Exception as e:
            logger.error(f"Error composing email: {e}")
            return f"Error composing email: {str(e)}"


class SendEmailInput(BaseModel):
    """Input schema for send_email tool."""

    to: List[str] = Field(description="List of recipient email addresses")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body content")
    cc: Optional[List[str]] = Field(default=None, description="CC recipients")


class SendEmailTool(BaseTool):
    """Tool to send an email."""

    name: str = "send_email"
    description: str = """
    Send an email immediately. Use this to send emails after composing and reviewing them.
    IMPORTANT: Always confirm with the user before sending emails.
    """
    args_schema: type[BaseModel] = SendEmailInput
    email_service: GmailService = Field(default_factory=GmailService)

    class Config:
        arbitrary_types_allowed = True

    def _run(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None
    ) -> str:
        """Send email."""
        try:
            draft = EmailDraft(
                to=to,
                subject=subject,
                body=body,
                cc=cc
            )

            success = self.email_service.send_message(draft)

            if success:
                return f"Email sent successfully!\n\nTo: {', '.join(to)}\nSubject: {subject}"
            else:
                return "Failed to send email."

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return f"Error sending email: {str(e)}"


class SearchEmailsInput(BaseModel):
    """Input schema for search_emails tool."""

    query: str = Field(description="Search query (e.g., 'from:user@example.com subject:meeting')")
    max_results: int = Field(default=10, description="Maximum number of results")


class SearchEmailsTool(BaseTool):
    """Tool to search emails."""

    name: str = "search_emails"
    description: str = """
    Search for emails using Gmail search syntax.
    Examples:
    - 'from:example@gmail.com' - emails from specific sender
    - 'subject:meeting' - emails with 'meeting' in subject
    - 'is:unread' - unread emails
    - 'has:attachment' - emails with attachments
    - 'after:2024/01/01' - emails after specific date
    """
    args_schema: type[BaseModel] = SearchEmailsInput
    email_service: GmailService = Field(default_factory=GmailService)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str, max_results: int = 10) -> str:
        """Search emails."""
        try:
            messages = self.email_service.search_messages(
                query=query,
                max_results=max_results
            )

            if not messages:
                return f"No emails found for query: {query}"

            result = f"Found {len(messages)} email(s) for query '{query}':\n\n"
            for i, msg in enumerate(messages, 1):
                result += f"{i}. [{msg.id}]\n"
                result += f"   From: {msg.sender}\n"
                result += f"   Subject: {msg.subject}\n"
                result += f"   Date: {msg.date}\n"
                result += f"   Preview: {msg.snippet[:100]}...\n\n"

            return result
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return f"Error searching emails: {str(e)}"


# List of all available tools
def get_email_tools(email_service: Optional[GmailService] = None) -> List[BaseTool]:
    """Get all email tools.

    Args:
        email_service: Optional GmailService instance

    Returns:
        List of email tools
    """
    service = email_service or GmailService()

    return [
        GetEmailsTool(email_service=service),
        ReadEmailTool(email_service=service),
        ComposeEmailTool(email_service=service),
        SendEmailTool(email_service=service),
        SearchEmailsTool(email_service=service),
    ]
