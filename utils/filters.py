"""Advanced email filtering system."""

from typing import List, Optional, Callable, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from services.base_email import EmailMessage
from utils.helpers import extract_email_address


class FilterOperator(Enum):
    """Filter operators."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


class FilterField(Enum):
    """Filterable fields."""

    SENDER = "sender"
    SUBJECT = "subject"
    BODY = "body"
    DATE = "date"
    IS_READ = "is_read"
    IS_STARRED = "is_starred"
    HAS_ATTACHMENT = "has_attachment"
    LABEL = "label"
    RECIPIENT = "recipient"


@dataclass
class FilterRule:
    """Email filter rule."""

    field: FilterField
    operator: FilterOperator
    value: Any
    case_sensitive: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field": self.field.value,
            "operator": self.operator.value,
            "value": self.value,
            "case_sensitive": self.case_sensitive
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilterRule":
        """Create from dictionary."""
        return cls(
            field=FilterField(data["field"]),
            operator=FilterOperator(data["operator"]),
            value=data["value"],
            case_sensitive=data.get("case_sensitive", False)
        )


class EmailFilter:
    """Advanced email filter."""

    def __init__(self):
        """Initialize filter."""
        self.rules: List[FilterRule] = []
        self.match_all: bool = True  # True = AND, False = OR

    def add_rule(
        self,
        field: FilterField,
        operator: FilterOperator,
        value: Any,
        case_sensitive: bool = False
    ) -> "EmailFilter":
        """Add filter rule.

        Args:
            field: Field to filter on
            operator: Filter operator
            value: Value to compare
            case_sensitive: Case sensitive comparison

        Returns:
            Self for chaining
        """
        rule = FilterRule(field, operator, value, case_sensitive)
        self.rules.append(rule)
        return self

    def set_match_mode(self, match_all: bool) -> "EmailFilter":
        """Set match mode.

        Args:
            match_all: True for AND, False for OR

        Returns:
            Self for chaining
        """
        self.match_all = match_all
        return self

    def clear_rules(self) -> "EmailFilter":
        """Clear all rules.

        Returns:
            Self for chaining
        """
        self.rules = []
        return self

    def apply(self, emails: List[EmailMessage]) -> List[EmailMessage]:
        """Apply filter to emails.

        Args:
            emails: List of emails

        Returns:
            Filtered emails
        """
        if not self.rules:
            return emails

        filtered = []

        for email in emails:
            if self.match_all:
                # AND logic - all rules must match
                if all(self._evaluate_rule(rule, email) for rule in self.rules):
                    filtered.append(email)
            else:
                # OR logic - any rule must match
                if any(self._evaluate_rule(rule, email) for rule in self.rules):
                    filtered.append(email)

        return filtered

    def _evaluate_rule(self, rule: FilterRule, email: EmailMessage) -> bool:
        """Evaluate a single rule.

        Args:
            rule: Filter rule
            email: Email message

        Returns:
            True if rule matches
        """
        # Get field value
        field_value = self._get_field_value(rule.field, email)

        # Apply operator
        return self._apply_operator(
            rule.operator,
            field_value,
            rule.value,
            rule.case_sensitive
        )

    def _get_field_value(self, field: FilterField, email: EmailMessage) -> Any:
        """Get field value from email.

        Args:
            field: Field to get
            email: Email message

        Returns:
            Field value
        """
        if field == FilterField.SENDER:
            return extract_email_address(email.sender)
        elif field == FilterField.SUBJECT:
            return email.subject
        elif field == FilterField.BODY:
            return email.body
        elif field == FilterField.DATE:
            return email.date
        elif field == FilterField.IS_READ:
            return email.is_read
        elif field == FilterField.IS_STARRED:
            return email.is_starred
        elif field == FilterField.HAS_ATTACHMENT:
            return email.attachments is not None and len(email.attachments) > 0
        elif field == FilterField.LABEL:
            return email.labels or []
        elif field == FilterField.RECIPIENT:
            return email.recipients
        else:
            return None

    def _apply_operator(
        self,
        operator: FilterOperator,
        field_value: Any,
        filter_value: Any,
        case_sensitive: bool
    ) -> bool:
        """Apply operator to values.

        Args:
            operator: Operator
            field_value: Value from email
            filter_value: Value to compare
            case_sensitive: Case sensitive

        Returns:
            True if condition matches
        """
        # Handle None values
        if field_value is None:
            return operator == FilterOperator.NOT_EQUALS

        # String operations
        if isinstance(field_value, str):
            if not case_sensitive:
                field_value = field_value.lower()
                if isinstance(filter_value, str):
                    filter_value = filter_value.lower()

            if operator == FilterOperator.EQUALS:
                return field_value == filter_value
            elif operator == FilterOperator.NOT_EQUALS:
                return field_value != filter_value
            elif operator == FilterOperator.CONTAINS:
                return filter_value in field_value
            elif operator == FilterOperator.NOT_CONTAINS:
                return filter_value not in field_value
            elif operator == FilterOperator.STARTS_WITH:
                return field_value.startswith(filter_value)
            elif operator == FilterOperator.ENDS_WITH:
                return field_value.endswith(filter_value)

        # List operations
        elif isinstance(field_value, list):
            if operator == FilterOperator.CONTAINS:
                return filter_value in field_value
            elif operator == FilterOperator.NOT_CONTAINS:
                return filter_value not in field_value
            elif operator == FilterOperator.IN_LIST:
                return any(item in filter_value for item in field_value)
            elif operator == FilterOperator.NOT_IN_LIST:
                return not any(item in filter_value for item in field_value)

        # Boolean operations
        elif isinstance(field_value, bool):
            if operator == FilterOperator.EQUALS:
                return field_value == filter_value

        # Datetime operations
        elif isinstance(field_value, datetime):
            if isinstance(filter_value, datetime):
                if operator == FilterOperator.EQUALS:
                    return field_value.date() == filter_value.date()
                elif operator == FilterOperator.GREATER_THAN:
                    return field_value > filter_value
                elif operator == FilterOperator.LESS_THAN:
                    return field_value < filter_value

        # Numeric operations
        elif isinstance(field_value, (int, float)):
            if operator == FilterOperator.EQUALS:
                return field_value == filter_value
            elif operator == FilterOperator.NOT_EQUALS:
                return field_value != filter_value
            elif operator == FilterOperator.GREATER_THAN:
                return field_value > filter_value
            elif operator == FilterOperator.LESS_THAN:
                return field_value < filter_value

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Export filter to dictionary.

        Returns:
            Filter configuration
        """
        return {
            "rules": [rule.to_dict() for rule in self.rules],
            "match_all": self.match_all
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailFilter":
        """Import filter from dictionary.

        Args:
            data: Filter configuration

        Returns:
            EmailFilter instance
        """
        filter_obj = cls()
        filter_obj.match_all = data.get("match_all", True)

        for rule_data in data.get("rules", []):
            rule = FilterRule.from_dict(rule_data)
            filter_obj.rules.append(rule)

        return filter_obj


class PresetFilters:
    """Preset filter configurations."""

    @staticmethod
    def unread_from_sender(sender: str) -> EmailFilter:
        """Filter unread emails from specific sender.

        Args:
            sender: Sender email

        Returns:
            EmailFilter
        """
        return EmailFilter() \
            .add_rule(FilterField.IS_READ, FilterOperator.EQUALS, False) \
            .add_rule(FilterField.SENDER, FilterOperator.EQUALS, sender) \
            .set_match_mode(True)

    @staticmethod
    def today_important() -> EmailFilter:
        """Filter today's important emails.

        Returns:
            EmailFilter
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        return EmailFilter() \
            .add_rule(FilterField.DATE, FilterOperator.GREATER_THAN, today) \
            .add_rule(FilterField.IS_STARRED, FilterOperator.EQUALS, True) \
            .set_match_mode(True)

    @staticmethod
    def unread_with_attachments() -> EmailFilter:
        """Filter unread emails with attachments.

        Returns:
            EmailFilter
        """
        return EmailFilter() \
            .add_rule(FilterField.IS_READ, FilterOperator.EQUALS, False) \
            .add_rule(FilterField.HAS_ATTACHMENT, FilterOperator.EQUALS, True) \
            .set_match_mode(True)

    @staticmethod
    def last_n_days(days: int) -> EmailFilter:
        """Filter emails from last N days.

        Args:
            days: Number of days

        Returns:
            EmailFilter
        """
        cutoff = datetime.now() - timedelta(days=days)

        return EmailFilter() \
            .add_rule(FilterField.DATE, FilterOperator.GREATER_THAN, cutoff)

    @staticmethod
    def subject_keywords(keywords: List[str], match_any: bool = False) -> EmailFilter:
        """Filter by subject keywords.

        Args:
            keywords: List of keywords
            match_any: True to match any keyword, False to match all

        Returns:
            EmailFilter
        """
        email_filter = EmailFilter().set_match_mode(not match_any)

        for keyword in keywords:
            email_filter.add_rule(
                FilterField.SUBJECT,
                FilterOperator.CONTAINS,
                keyword,
                case_sensitive=False
            )

        return email_filter

    @staticmethod
    def exclude_senders(senders: List[str]) -> EmailFilter:
        """Exclude emails from specific senders.

        Args:
            senders: List of sender emails

        Returns:
            EmailFilter
        """
        email_filter = EmailFilter().set_match_mode(True)

        for sender in senders:
            email_filter.add_rule(
                FilterField.SENDER,
                FilterOperator.NOT_EQUALS,
                sender
            )

        return email_filter


def create_custom_filter() -> EmailFilter:
    """Create a new custom filter.

    Returns:
        Empty EmailFilter
    """
    return EmailFilter()
