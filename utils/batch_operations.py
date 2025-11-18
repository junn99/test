"""Batch operations for emails."""

from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from services.base_email import BaseEmailService


class BatchActionType(Enum):
    """Batch action types."""

    MARK_READ = "mark_read"
    MARK_UNREAD = "mark_unread"
    DELETE = "delete"
    ARCHIVE = "archive"
    STAR = "star"
    UNSTAR = "unstar"
    APPLY_LABEL = "apply_label"
    REMOVE_LABEL = "remove_label"


@dataclass
class BatchResult:
    """Result of batch operation."""

    total: int
    succeeded: int
    failed: int
    errors: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "success_rate": f"{(self.succeeded / self.total * 100):.1f}%" if self.total > 0 else "0%",
            "errors": self.errors
        }

    def __str__(self) -> str:
        """String representation."""
        success_rate = (self.succeeded / self.total * 100) if self.total > 0 else 0
        return (
            f"Batch operation completed: "
            f"{self.succeeded}/{self.total} succeeded ({success_rate:.1f}%), "
            f"{self.failed} failed"
        )


class BatchOperations:
    """Batch operations handler."""

    def __init__(self, email_service: BaseEmailService):
        """Initialize batch operations.

        Args:
            email_service: Email service instance
        """
        self.email_service = email_service

    def execute_batch(
        self,
        message_ids: List[str],
        action: BatchActionType,
        **kwargs
    ) -> BatchResult:
        """Execute batch action on multiple emails.

        Args:
            message_ids: List of message IDs
            action: Batch action type
            **kwargs: Additional arguments for the action

        Returns:
            BatchResult object
        """
        total = len(message_ids)
        succeeded = 0
        failed = 0
        errors = []

        logger.info(f"Starting batch operation: {action.value} on {total} messages")

        # Map action to method
        action_map = {
            BatchActionType.MARK_READ: self._mark_read,
            BatchActionType.MARK_UNREAD: self._mark_unread,
            BatchActionType.DELETE: self._delete,
            BatchActionType.STAR: lambda mid: self._modify_labels(mid, add=["STARRED"]),
            BatchActionType.UNSTAR: lambda mid: self._modify_labels(mid, remove=["STARRED"]),
            BatchActionType.ARCHIVE: lambda mid: self._modify_labels(mid, remove=["INBOX"]),
        }

        # Get action function
        action_func = action_map.get(action)

        if not action_func:
            logger.error(f"Unsupported batch action: {action}")
            return BatchResult(total=total, succeeded=0, failed=total, errors=[
                {"error": f"Unsupported action: {action}"}
            ])

        # Execute action on each message
        for message_id in message_ids:
            try:
                success = action_func(message_id)
                if success:
                    succeeded += 1
                else:
                    failed += 1
                    errors.append({
                        "message_id": message_id,
                        "error": "Operation returned False"
                    })
            except Exception as e:
                failed += 1
                errors.append({
                    "message_id": message_id,
                    "error": str(e)
                })
                logger.error(f"Error processing {message_id}: {e}")

        result = BatchResult(
            total=total,
            succeeded=succeeded,
            failed=failed,
            errors=errors
        )

        logger.info(str(result))
        return result

    def _mark_read(self, message_id: str) -> bool:
        """Mark message as read."""
        return self.email_service.mark_as_read(message_id)

    def _mark_unread(self, message_id: str) -> bool:
        """Mark message as unread."""
        return self.email_service.mark_as_unread(message_id)

    def _delete(self, message_id: str) -> bool:
        """Delete message."""
        return self.email_service.delete_message(message_id)

    def _modify_labels(
        self,
        message_id: str,
        add: Optional[List[str]] = None,
        remove: Optional[List[str]] = None
    ) -> bool:
        """Modify message labels (Gmail specific).

        Args:
            message_id: Message ID
            add: Labels to add
            remove: Labels to remove

        Returns:
            True if successful
        """
        # This is Gmail-specific, needs implementation in gmail_service.py
        try:
            from services.gmail_service import GmailService
            if isinstance(self.email_service, GmailService):
                service = self.email_service.service
                body = {}

                if add:
                    body["addLabelIds"] = add
                if remove:
                    body["removeLabelIds"] = remove

                service.users().messages().modify(
                    userId=self.email_service.user_id,
                    id=message_id,
                    body=body
                ).execute()

                return True
        except Exception as e:
            logger.error(f"Error modifying labels: {e}")
            return False

        return False

    def batch_mark_read(self, message_ids: List[str]) -> BatchResult:
        """Mark multiple messages as read.

        Args:
            message_ids: List of message IDs

        Returns:
            BatchResult
        """
        return self.execute_batch(message_ids, BatchActionType.MARK_READ)

    def batch_mark_unread(self, message_ids: List[str]) -> BatchResult:
        """Mark multiple messages as unread.

        Args:
            message_ids: List of message IDs

        Returns:
            BatchResult
        """
        return self.execute_batch(message_ids, BatchActionType.MARK_UNREAD)

    def batch_delete(self, message_ids: List[str]) -> BatchResult:
        """Delete multiple messages.

        Args:
            message_ids: List of message IDs

        Returns:
            BatchResult
        """
        return self.execute_batch(message_ids, BatchActionType.DELETE)

    def batch_star(self, message_ids: List[str]) -> BatchResult:
        """Star multiple messages.

        Args:
            message_ids: List of message IDs

        Returns:
            BatchResult
        """
        return self.execute_batch(message_ids, BatchActionType.STAR)

    def batch_unstar(self, message_ids: List[str]) -> BatchResult:
        """Unstar multiple messages.

        Args:
            message_ids: List of message IDs

        Returns:
            BatchResult
        """
        return self.execute_batch(message_ids, BatchActionType.UNSTAR)

    def batch_archive(self, message_ids: List[str]) -> BatchResult:
        """Archive multiple messages.

        Args:
            message_ids: List of message IDs

        Returns:
            BatchResult
        """
        return self.execute_batch(message_ids, BatchActionType.ARCHIVE)

    def filter_and_execute(
        self,
        filter_func: Callable,
        action: BatchActionType,
        max_count: Optional[int] = None,
        **kwargs
    ) -> BatchResult:
        """Filter emails and execute batch action.

        Args:
            filter_func: Function to filter emails (returns List[EmailMessage])
            action: Batch action to execute
            max_count: Maximum number of emails to process
            **kwargs: Additional arguments for action

        Returns:
            BatchResult
        """
        try:
            # Get filtered messages
            messages = filter_func()

            if max_count:
                messages = messages[:max_count]

            # Extract message IDs
            message_ids = [msg.id for msg in messages]

            # Execute batch action
            return self.execute_batch(message_ids, action, **kwargs)

        except Exception as e:
            logger.error(f"Error in filter_and_execute: {e}")
            return BatchResult(
                total=0,
                succeeded=0,
                failed=0,
                errors=[{"error": str(e)}]
            )


def create_batch_operations(email_service: BaseEmailService) -> BatchOperations:
    """Create BatchOperations instance.

    Args:
        email_service: Email service

    Returns:
        BatchOperations instance
    """
    return BatchOperations(email_service)
