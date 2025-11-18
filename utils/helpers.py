"""Helper utility functions."""

import re
from typing import List, Optional
from datetime import datetime, timedelta
from email.utils import parseaddr


def validate_email(email: str) -> bool:
    """Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def parse_email_list(email_string: str) -> List[str]:
    """Parse comma-separated email addresses.

    Args:
        email_string: Comma-separated email addresses

    Returns:
        List of valid email addresses
    """
    emails = [email.strip() for email in email_string.split(",")]
    return [email for email in emails if validate_email(email)]


def extract_email_address(email_string: str) -> str:
    """Extract email address from string like 'Name <email@example.com>'.

    Args:
        email_string: Email string

    Returns:
        Email address
    """
    name, email = parseaddr(email_string)
    return email


def format_email_date(date: datetime) -> str:
    """Format email date in human-readable format.

    Args:
        date: Datetime object

    Returns:
        Formatted date string
    """
    now = datetime.now(date.tzinfo)
    diff = now - date

    if diff.days == 0:
        # Today
        if diff.seconds < 3600:
            # Less than 1 hour
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days} days ago"
    else:
        return date.strftime("%b %d, %Y")


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text.

    Args:
        text: Text containing URLs

    Returns:
        List of URLs
    """
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)


def sanitize_html(html: str) -> str:
    """Remove potentially dangerous HTML tags.

    Args:
        html: HTML content

    Returns:
        Sanitized HTML
    """
    # Remove script tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove style tags
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove onclick and other event handlers
    html = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)

    return html


def parse_gmail_query(query_dict: dict) -> str:
    """Build Gmail search query from dictionary.

    Args:
        query_dict: Dictionary with query parameters

    Returns:
        Gmail search query string

    Example:
        >>> parse_gmail_query({"from": "user@example.com", "subject": "meeting"})
        'from:user@example.com subject:meeting'
    """
    query_parts = []

    for key, value in query_dict.items():
        if value:
            query_parts.append(f"{key}:{value}")

    return " ".join(query_parts)


def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Estimate reading time for text.

    Args:
        text: Text content
        words_per_minute: Average reading speed

    Returns:
        Estimated reading time in minutes
    """
    word_count = len(text.split())
    minutes = word_count / words_per_minute
    return max(1, int(minutes))


def group_emails_by_thread(emails: List) -> dict:
    """Group emails by thread ID.

    Args:
        emails: List of EmailMessage objects

    Returns:
        Dictionary mapping thread_id to list of emails
    """
    threads = {}

    for email in emails:
        thread_id = email.thread_id

        if thread_id not in threads:
            threads[thread_id] = []

        threads[thread_id].append(email)

    return threads


def prioritize_emails(emails: List) -> List:
    """Prioritize emails based on importance factors.

    Args:
        emails: List of EmailMessage objects

    Returns:
        Sorted list of emails by priority
    """
    def priority_score(email):
        """Calculate priority score for email."""
        score = 0

        # Unread emails get higher priority
        if not email.is_read:
            score += 10

        # Starred emails get higher priority
        if email.is_starred:
            score += 5

        # Recent emails get higher priority
        age_hours = (datetime.now(email.date.tzinfo) - email.date).total_seconds() / 3600
        if age_hours < 1:
            score += 8
        elif age_hours < 24:
            score += 5
        elif age_hours < 168:  # 1 week
            score += 2

        # Emails with attachments might be important
        if email.attachments and len(email.attachments) > 0:
            score += 3

        return score

    return sorted(emails, key=priority_score, reverse=True)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} PB"
