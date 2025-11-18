"""User profile and preferences management."""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ..utils.config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class UserProfile:
    """Manages user preferences and learned behaviors."""

    def __init__(self, profile_name: str = "default"):
        self.profile_name = profile_name
        self.profile_path = settings.profiles_dir / f"{profile_name}.json"
        self.profile_data = self._load_profile()

    def _load_profile(self) -> Dict[str, Any]:
        """Load profile from disk or create new one."""
        if self.profile_path.exists():
            logger.info(f"Loading profile: {self.profile_name}")
            with open(self.profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            logger.info(f"Creating new profile: {self.profile_name}")
            return self._create_default_profile()

    def _create_default_profile(self) -> Dict[str, Any]:
        """Create default profile structure."""
        return {
            "profile_name": self.profile_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "preferences": {
                "report_style": "concise",  # concise, detailed, technical
                "report_frequency": "weekly",  # daily, weekly, monthly
                "content_structure": "bullet_points",  # bullet_points, paragraphs, mixed
                "language_tone": "professional",  # professional, casual, academic
            },
            "learned_patterns": {
                "common_keywords": [],
                "frequent_tags": [],
                "writing_style_notes": "",
                "preferred_page_types": [],
            },
            "statistics": {
                "total_pages_analyzed": 0,
                "reports_generated": 0,
                "last_sync": None,
            }
        }

    def save(self):
        """Save profile to disk."""
        self.profile_data["updated_at"] = datetime.now().isoformat()
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(self.profile_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Profile saved: {self.profile_name}")

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a preference value."""
        return self.profile_data.get("preferences", {}).get(key, default)

    def set_preference(self, key: str, value: Any):
        """Set a preference value."""
        if "preferences" not in self.profile_data:
            self.profile_data["preferences"] = {}

        self.profile_data["preferences"][key] = value
        self.save()

    def update_statistics(self, **kwargs):
        """Update statistics."""
        if "statistics" not in self.profile_data:
            self.profile_data["statistics"] = {}

        for key, value in kwargs.items():
            self.profile_data["statistics"][key] = value

        self.save()

    def add_learned_pattern(self, pattern_type: str, value: Any):
        """Add a learned pattern."""
        if "learned_patterns" not in self.profile_data:
            self.profile_data["learned_patterns"] = {}

        if pattern_type not in self.profile_data["learned_patterns"]:
            self.profile_data["learned_patterns"][pattern_type] = []

        if isinstance(self.profile_data["learned_patterns"][pattern_type], list):
            if value not in self.profile_data["learned_patterns"][pattern_type]:
                self.profile_data["learned_patterns"][pattern_type].append(value)
        else:
            self.profile_data["learned_patterns"][pattern_type] = value

        self.save()

    def get_profile_summary(self) -> str:
        """Get a text summary of the user profile."""
        prefs = self.profile_data.get("preferences", {})
        patterns = self.profile_data.get("learned_patterns", {})
        stats = self.profile_data.get("statistics", {})

        summary = f"""
User Profile Summary:
- Report Style: {prefs.get('report_style', 'N/A')}
- Report Frequency: {prefs.get('report_frequency', 'N/A')}
- Content Structure: {prefs.get('content_structure', 'N/A')}
- Language Tone: {prefs.get('language_tone', 'N/A')}

Learned Patterns:
- Common Keywords: {', '.join(patterns.get('common_keywords', [])[:10])}
- Frequent Tags: {', '.join(patterns.get('frequent_tags', [])[:10])}

Statistics:
- Total Pages Analyzed: {stats.get('total_pages_analyzed', 0)}
- Reports Generated: {stats.get('reports_generated', 0)}
- Last Sync: {stats.get('last_sync', 'Never')}
"""
        return summary.strip()
