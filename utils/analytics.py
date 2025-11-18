"""Email analytics and statistics."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass

from services.base_email import EmailMessage
from utils.helpers import extract_email_address


@dataclass
class EmailStats:
    """Email statistics data."""

    total_emails: int
    unread_count: int
    starred_count: int
    today_count: int
    this_week_count: int
    this_month_count: int

    top_senders: List[Dict[str, Any]]
    emails_by_hour: Dict[int, int]
    emails_by_day: Dict[str, int]
    emails_by_month: Dict[str, int]

    average_per_day: float
    read_rate: float
    response_rate: float

    labels_distribution: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_emails": self.total_emails,
            "unread_count": self.unread_count,
            "starred_count": self.starred_count,
            "today_count": self.today_count,
            "this_week_count": self.this_week_count,
            "this_month_count": self.this_month_count,
            "top_senders": self.top_senders,
            "emails_by_hour": self.emails_by_hour,
            "emails_by_day": self.emails_by_day,
            "emails_by_month": self.emails_by_month,
            "average_per_day": self.average_per_day,
            "read_rate": self.read_rate,
            "response_rate": self.response_rate,
            "labels_distribution": self.labels_distribution,
        }


class EmailAnalytics:
    """Analyze email data and generate statistics."""

    def __init__(self, emails: List[EmailMessage]):
        """Initialize analytics.

        Args:
            emails: List of email messages
        """
        self.emails = emails
        self.now = datetime.now()

    def generate_stats(self) -> EmailStats:
        """Generate comprehensive email statistics.

        Returns:
            EmailStats object
        """
        if not self.emails:
            return self._empty_stats()

        # Basic counts
        total = len(self.emails)
        unread = sum(1 for e in self.emails if not e.is_read)
        starred = sum(1 for e in self.emails if e.is_starred)

        # Time-based counts
        today_count = self._count_emails_since(days=0)
        week_count = self._count_emails_since(days=7)
        month_count = self._count_emails_since(days=30)

        # Top senders
        top_senders = self._get_top_senders(limit=10)

        # Time distribution
        by_hour = self._get_emails_by_hour()
        by_day = self._get_emails_by_day()
        by_month = self._get_emails_by_month()

        # Averages and rates
        avg_per_day = self._calculate_average_per_day()
        read_rate = (total - unread) / total * 100 if total > 0 else 0
        response_rate = self._estimate_response_rate()

        # Labels
        labels_dist = self._get_labels_distribution()

        return EmailStats(
            total_emails=total,
            unread_count=unread,
            starred_count=starred,
            today_count=today_count,
            this_week_count=week_count,
            this_month_count=month_count,
            top_senders=top_senders,
            emails_by_hour=by_hour,
            emails_by_day=by_day,
            emails_by_month=by_month,
            average_per_day=avg_per_day,
            read_rate=read_rate,
            response_rate=response_rate,
            labels_distribution=labels_dist,
        )

    def _empty_stats(self) -> EmailStats:
        """Return empty statistics."""
        return EmailStats(
            total_emails=0,
            unread_count=0,
            starred_count=0,
            today_count=0,
            this_week_count=0,
            this_month_count=0,
            top_senders=[],
            emails_by_hour={},
            emails_by_day={},
            emails_by_month={},
            average_per_day=0.0,
            read_rate=0.0,
            response_rate=0.0,
            labels_distribution={},
        )

    def _count_emails_since(self, days: int) -> int:
        """Count emails since N days ago.

        Args:
            days: Number of days to look back

        Returns:
            Count of emails
        """
        if days == 0:
            # Today
            cutoff = self.now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            cutoff = self.now - timedelta(days=days)

        return sum(1 for e in self.emails if e.date >= cutoff)

    def _get_top_senders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top email senders.

        Args:
            limit: Maximum number of senders

        Returns:
            List of sender info dictionaries
        """
        sender_counts = Counter()

        for email in self.emails:
            sender = extract_email_address(email.sender)
            sender_counts[sender] += 1

        top_senders = []
        for sender, count in sender_counts.most_common(limit):
            percentage = (count / len(self.emails)) * 100
            top_senders.append({
                "email": sender,
                "count": count,
                "percentage": round(percentage, 1)
            })

        return top_senders

    def _get_emails_by_hour(self) -> Dict[int, int]:
        """Get email distribution by hour of day.

        Returns:
            Dictionary mapping hour (0-23) to count
        """
        by_hour = defaultdict(int)

        for email in self.emails:
            hour = email.date.hour
            by_hour[hour] += 1

        return dict(by_hour)

    def _get_emails_by_day(self) -> Dict[str, int]:
        """Get email distribution by day of week.

        Returns:
            Dictionary mapping day name to count
        """
        by_day = defaultdict(int)
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for email in self.emails:
            day_idx = email.date.weekday()
            day_name = day_names[day_idx]
            by_day[day_name] += 1

        return dict(by_day)

    def _get_emails_by_month(self) -> Dict[str, int]:
        """Get email distribution by month.

        Returns:
            Dictionary mapping month to count
        """
        by_month = defaultdict(int)

        for email in self.emails:
            month_str = email.date.strftime("%Y-%m")
            by_month[month_str] += 1

        return dict(sorted(by_month.items()))

    def _calculate_average_per_day(self) -> float:
        """Calculate average emails per day.

        Returns:
            Average emails per day
        """
        if not self.emails:
            return 0.0

        # Get date range
        dates = [e.date.date() for e in self.emails]
        oldest = min(dates)
        newest = max(dates)

        days = (newest - oldest).days + 1

        if days == 0:
            return float(len(self.emails))

        return len(self.emails) / days

    def _estimate_response_rate(self) -> float:
        """Estimate response rate (simplified).

        Returns:
            Estimated response rate percentage
        """
        # Simple estimation: ratio of sent to received
        # This is a simplified version
        # In real implementation, would need to analyze threads

        if not self.emails:
            return 0.0

        # Count emails with "Re:" in subject (rough approximation)
        responses = sum(1 for e in self.emails if e.subject.startswith("Re:"))

        return (responses / len(self.emails)) * 100 if self.emails else 0.0

    def _get_labels_distribution(self) -> Dict[str, int]:
        """Get distribution of email labels.

        Returns:
            Dictionary mapping label to count
        """
        label_counts = defaultdict(int)

        for email in self.emails:
            if email.labels:
                for label in email.labels:
                    # Skip system labels like UNREAD, IMPORTANT
                    if label not in ["UNREAD", "STARRED", "IMPORTANT", "CATEGORY_PERSONAL"]:
                        label_counts[label] += 1

        return dict(label_counts)

    def get_sender_timeline(self, sender_email: str) -> Dict[str, Any]:
        """Get timeline of emails from specific sender.

        Args:
            sender_email: Sender email address

        Returns:
            Timeline data
        """
        sender_emails = [
            e for e in self.emails
            if extract_email_address(e.sender) == sender_email
        ]

        if not sender_emails:
            return {
                "sender": sender_email,
                "total": 0,
                "timeline": {}
            }

        # Group by month
        timeline = defaultdict(int)
        for email in sender_emails:
            month_str = email.date.strftime("%Y-%m")
            timeline[month_str] += 1

        return {
            "sender": sender_email,
            "total": len(sender_emails),
            "timeline": dict(sorted(timeline.items()))
        }

    def get_busiest_times(self) -> Dict[str, Any]:
        """Get busiest times for receiving emails.

        Returns:
            Busiest times data
        """
        if not self.emails:
            return {
                "busiest_hour": None,
                "busiest_day": None,
                "busiest_month": None
            }

        by_hour = self._get_emails_by_hour()
        by_day = self._get_emails_by_day()
        by_month = self._get_emails_by_month()

        busiest_hour = max(by_hour.items(), key=lambda x: x[1]) if by_hour else (None, 0)
        busiest_day = max(by_day.items(), key=lambda x: x[1]) if by_day else (None, 0)
        busiest_month = max(by_month.items(), key=lambda x: x[1]) if by_month else (None, 0)

        return {
            "busiest_hour": {
                "hour": busiest_hour[0],
                "count": busiest_hour[1]
            } if busiest_hour[0] is not None else None,
            "busiest_day": {
                "day": busiest_day[0],
                "count": busiest_day[1]
            } if busiest_day[0] is not None else None,
            "busiest_month": {
                "month": busiest_month[0],
                "count": busiest_month[1]
            } if busiest_month[0] is not None else None,
        }

    def get_productivity_insights(self) -> Dict[str, Any]:
        """Get productivity insights.

        Returns:
            Productivity insights
        """
        stats = self.generate_stats()

        # Calculate insights
        inbox_zero_days = self._count_inbox_zero_days()
        response_time_avg = self._estimate_average_response_time()

        return {
            "unread_percentage": (stats.unread_count / stats.total_emails * 100) if stats.total_emails > 0 else 0,
            "inbox_zero_days": inbox_zero_days,
            "average_response_time_hours": response_time_avg,
            "emails_per_day": stats.average_per_day,
            "read_rate": stats.read_rate,
            "recommendation": self._generate_recommendation(stats)
        }

    def _count_inbox_zero_days(self) -> int:
        """Count days with zero unread emails (simplified).

        Returns:
            Count of inbox zero days
        """
        # Simplified version
        # In real implementation, would track daily snapshots
        return 0  # Placeholder

    def _estimate_average_response_time(self) -> float:
        """Estimate average response time in hours (simplified).

        Returns:
            Average response time in hours
        """
        # Simplified version
        # In real implementation, would analyze email threads
        return 24.0  # Placeholder (24 hours)

    def _generate_recommendation(self, stats: EmailStats) -> str:
        """Generate productivity recommendation.

        Args:
            stats: Email statistics

        Returns:
            Recommendation string
        """
        if stats.unread_count > stats.total_emails * 0.5:
            return "높은 미확인 메일 비율입니다. 배치 작업으로 일괄 처리를 고려해보세요."
        elif stats.average_per_day > 50:
            return "일일 평균 메일이 많습니다. 필터링 규칙 설정을 권장합니다."
        elif stats.read_rate > 90:
            return "훌륭한 메일 관리 습관입니다! 계속 유지하세요."
        else:
            return "안정적인 메일 관리 상태입니다."


def create_analytics(emails: List[EmailMessage]) -> EmailAnalytics:
    """Create EmailAnalytics instance.

    Args:
        emails: List of emails

    Returns:
        EmailAnalytics instance
    """
    return EmailAnalytics(emails)
