"""Analysis tools for Notion content."""
from collections import Counter
from typing import List, Dict, Any, Tuple
import re
from datetime import datetime

from langchain_core.tools import tool

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ContentAnalyzer:
    """Analyzes Notion content for patterns and insights."""

    def __init__(self):
        # Common Korean/English stop words
        self.stop_words = set([
            # English
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
            "be", "have", "has", "had", "do", "does", "did", "will", "would",
            "should", "could", "may", "might", "can", "this", "that", "these",
            "those", "i", "you", "he", "she", "it", "we", "they", "me", "him",
            "her", "us", "them", "my", "your", "his", "its", "our", "their",
            # Korean
            "이", "그", "저", "것", "수", "등", "및", "또는", "그리고", "하지만",
            "의", "가", "이", "은", "는", "을", "를", "에", "에서", "로", "으로",
            "와", "과", "도", "만", "까지", "부터", "하다", "되다", "있다", "없다",
        ])

    @tool
    def extract_keywords(self, text: str, top_n: int = 20) -> List[Tuple[str, int]]:
        """
        Extract top keywords from text using simple frequency analysis.

        Args:
            text: Text to analyze.
            top_n: Number of top keywords to return.

        Returns:
            List of (keyword, frequency) tuples.
        """
        if not text:
            return []

        # Clean and tokenize
        text = text.lower()
        # Remove special characters but keep Korean/English/numbers
        words = re.findall(r'[가-힣a-z0-9]+', text)

        # Filter out stop words and short words
        filtered_words = [
            word for word in words
            if word not in self.stop_words and len(word) > 1
        ]

        # Count frequencies
        word_freq = Counter(filtered_words)

        # Get top N
        top_keywords = word_freq.most_common(top_n)

        logger.info(f"Extracted {len(top_keywords)} keywords from text")
        return top_keywords

    @tool
    def extract_tags(self, pages: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Extract and count tags/hashtags from pages.

        Args:
            pages: List of page dictionaries with content.

        Returns:
            Dictionary of tag -> frequency.
        """
        tag_counter = Counter()

        for page in pages:
            content = page.get("content", "")
            title = page.get("title", "")

            # Combine title and content
            full_text = f"{title} {content}"

            # Find hashtags
            hashtags = re.findall(r'#([가-힣a-zA-Z0-9_]+)', full_text)
            tag_counter.update(hashtags)

            # Find @tags
            at_tags = re.findall(r'@([가-힣a-zA-Z0-9_]+)', full_text)
            tag_counter.update(at_tags)

        logger.info(f"Found {len(tag_counter)} unique tags")
        return dict(tag_counter)

    @tool
    def analyze_writing_patterns(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze writing patterns from pages.

        Args:
            pages: List of page dictionaries with content.

        Returns:
            Dictionary with pattern analysis.
        """
        if not pages:
            return {}

        total_words = 0
        total_chars = 0
        total_lines = 0
        sentence_lengths = []

        for page in pages:
            content = page.get("content", "")

            if not content:
                continue

            # Count words (approximate for mixed Korean/English)
            words = re.findall(r'[가-힣a-zA-Z]+', content)
            total_words += len(words)

            # Count characters
            total_chars += len(content)

            # Count lines
            lines = content.split('\n')
            total_lines += len(lines)

            # Sentence lengths (split by period, question mark, exclamation)
            sentences = re.split(r'[.?!。]+', content)
            sentence_lengths.extend([len(s.split()) for s in sentences if s.strip()])

        avg_words_per_page = total_words / len(pages) if pages else 0
        avg_chars_per_page = total_chars / len(pages) if pages else 0
        avg_lines_per_page = total_lines / len(pages) if pages else 0
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0

        analysis = {
            "total_pages": len(pages),
            "total_words": total_words,
            "total_characters": total_chars,
            "avg_words_per_page": round(avg_words_per_page, 2),
            "avg_chars_per_page": round(avg_chars_per_page, 2),
            "avg_lines_per_page": round(avg_lines_per_page, 2),
            "avg_sentence_length": round(avg_sentence_length, 2),
        }

        logger.info(f"Analyzed writing patterns from {len(pages)} pages")
        return analysis

    @tool
    def analyze_activity_patterns(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze activity patterns (time of edits, frequency, etc.).

        Args:
            pages: List of page dictionaries with last_edited_time.

        Returns:
            Dictionary with activity analysis.
        """
        if not pages:
            return {}

        # Extract edit times
        edit_times = []
        hours_counter = Counter()
        days_counter = Counter()

        for page in pages:
            last_edited = page.get("last_edited_time")
            if not last_edited:
                continue

            try:
                dt = datetime.fromisoformat(last_edited.replace("Z", "+00:00"))
                edit_times.append(dt)

                # Count by hour
                hours_counter[dt.hour] += 1

                # Count by day of week
                day_name = dt.strftime("%A")
                days_counter[day_name] += 1

            except Exception as e:
                logger.warning(f"Error parsing date {last_edited}: {e}")
                continue

        if not edit_times:
            return {}

        # Find most active hour
        most_active_hour = hours_counter.most_common(1)[0] if hours_counter else (0, 0)

        # Find most active day
        most_active_day = days_counter.most_common(1)[0] if days_counter else ("Unknown", 0)

        analysis = {
            "total_edits": len(edit_times),
            "most_active_hour": f"{most_active_hour[0]:02d}:00",
            "most_active_hour_count": most_active_hour[1],
            "most_active_day": most_active_day[0],
            "most_active_day_count": most_active_day[1],
            "hourly_distribution": dict(hours_counter),
            "daily_distribution": dict(days_counter),
        }

        logger.info(f"Analyzed activity patterns from {len(edit_times)} edits")
        return analysis

    @tool
    def generate_insights(self, pages: List[Dict[str, Any]]) -> List[str]:
        """
        Generate insights from analyzed data.

        Args:
            pages: List of page dictionaries.

        Returns:
            List of insight strings.
        """
        insights = []

        if not pages:
            return ["No data available for analysis."]

        # Analyze writing patterns
        writing_patterns = self.analyze_writing_patterns(pages)

        if writing_patterns.get("avg_words_per_page", 0) > 500:
            insights.append("📝 당신은 상세한 문서를 작성하는 경향이 있습니다.")
        elif writing_patterns.get("avg_words_per_page", 0) < 100:
            insights.append("📝 간결한 메모 스타일을 선호하시는군요.")

        # Analyze activity
        activity = self.analyze_activity_patterns(pages)

        if activity:
            hour = int(activity.get("most_active_hour", "0").split(":")[0])
            if 6 <= hour <= 12:
                insights.append("☀️ 오전 시간에 가장 활발하게 작업하시네요.")
            elif 13 <= hour <= 18:
                insights.append("🌤️ 오후 시간대에 주로 작업하십니다.")
            elif 19 <= hour <= 23:
                insights.append("🌙 저녁 시간에 집중력이 높으시네요.")
            else:
                insights.append("🌃 야간 작업을 선호하시는군요.")

        # Extract keywords
        all_text = " ".join([
            f"{page.get('title', '')} {page.get('content', '')}"
            for page in pages
        ])
        keywords = self.extract_keywords(all_text, top_n=5)

        if keywords:
            top_keywords = [kw[0] for kw in keywords[:3]]
            insights.append(f"🔑 주요 관심사: {', '.join(top_keywords)}")

        return insights

    def get_tools(self):
        """Get all analysis tools as a list."""
        return [
            self.extract_keywords,
            self.extract_tags,
            self.analyze_writing_patterns,
            self.analyze_activity_patterns,
            self.generate_insights,
        ]
