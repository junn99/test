"""Email template management."""

import json
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from loguru import logger


@dataclass
class EmailTemplate:
    """Email template structure."""

    id: str
    name: str
    subject: str
    body: str
    category: str = "General"
    variables: Optional[List[str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailTemplate":
        """Create from dictionary."""
        return cls(**data)


class TemplateManager:
    """Manage email templates."""

    def __init__(self, templates_file: str = "email_templates.json"):
        """Initialize template manager.

        Args:
            templates_file: Path to templates JSON file
        """
        self.templates_file = templates_file
        self.templates: Dict[str, EmailTemplate] = {}
        self._load_templates()

    def _load_templates(self):
        """Load templates from file."""
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.templates = {
                        tid: EmailTemplate.from_dict(tpl)
                        for tid, tpl in data.items()
                    }
                logger.info(f"Loaded {len(self.templates)} templates")
            except Exception as e:
                logger.error(f"Error loading templates: {e}")
                self.templates = {}
        else:
            # Create default templates
            self._create_default_templates()
            self._save_templates()

    def _save_templates(self):
        """Save templates to file."""
        try:
            data = {tid: tpl.to_dict() for tid, tpl in self.templates.items()}
            with open(self.templates_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.templates)} templates")
        except Exception as e:
            logger.error(f"Error saving templates: {e}")

    def _create_default_templates(self):
        """Create default email templates."""
        default_templates = [
            EmailTemplate(
                id="meeting_request",
                name="회의 요청",
                subject="회의 일정 협의 요청",
                body="""안녕하세요,

{날짜}에 {주제}에 대해 논의하고자 회의를 요청드립니다.

일시: {날짜} {시간}
장소: {장소}
안건: {주제}

참석 가능 여부를 회신 부탁드립니다.

감사합니다.""",
                category="회의",
                variables=["날짜", "시간", "장소", "주제"],
                created_at=datetime.now().isoformat(),
            ),
            EmailTemplate(
                id="follow_up",
                name="후속 조치 요청",
                subject="Re: {원제목} - 후속 조치",
                body="""안녕하세요,

{날짜}에 논의된 {주제}에 대한 후속 조치 요청드립니다.

진행 상황:
- {진행사항1}
- {진행사항2}

다음 단계:
- {다음단계1}
- {다음단계2}

회신 부탁드립니다.

감사합니다.""",
                category="후속조치",
                variables=["날짜", "주제", "원제목", "진행사항1", "진행사항2", "다음단계1", "다음단계2"],
                created_at=datetime.now().isoformat(),
            ),
            EmailTemplate(
                id="thank_you",
                name="감사 메일",
                subject="감사합니다",
                body="""안녕하세요,

{사유}에 대해 진심으로 감사드립니다.

{추가내용}

앞으로도 잘 부탁드립니다.

감사합니다.""",
                category="감사",
                variables=["사유", "추가내용"],
                created_at=datetime.now().isoformat(),
            ),
            EmailTemplate(
                id="status_update",
                name="상태 업데이트",
                subject="{프로젝트명} 진행 상황 업데이트",
                body="""안녕하세요,

{프로젝트명} 진행 상황을 공유드립니다.

■ 완료된 작업:
{완료작업}

■ 진행 중인 작업:
{진행중작업}

■ 예정된 작업:
{예정작업}

■ 이슈사항:
{이슈}

문의사항 있으시면 언제든 연락 부탁드립니다.

감사합니다.""",
                category="업데이트",
                variables=["프로젝트명", "완료작업", "진행중작업", "예정작업", "이슈"],
                created_at=datetime.now().isoformat(),
            ),
            EmailTemplate(
                id="introduction",
                name="소개 메일",
                subject="안녕하세요, {이름}입니다",
                body="""안녕하세요,

{소속} {직책} {이름}입니다.

{소개내용}

앞으로 {협업내용} 관련하여 협업하게 되어 기쁩니다.

필요하신 사항이나 문의사항 있으시면 언제든 연락 주시기 바랍니다.

감사합니다.""",
                category="소개",
                variables=["이름", "소속", "직책", "소개내용", "협업내용"],
                created_at=datetime.now().isoformat(),
            ),
        ]

        for tpl in default_templates:
            self.templates[tpl.id] = tpl

    def get_all_templates(self) -> List[EmailTemplate]:
        """Get all templates.

        Returns:
            List of email templates
        """
        return list(self.templates.values())

    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get template by ID.

        Args:
            template_id: Template ID

        Returns:
            EmailTemplate or None
        """
        return self.templates.get(template_id)

    def get_templates_by_category(self, category: str) -> List[EmailTemplate]:
        """Get templates by category.

        Args:
            category: Category name

        Returns:
            List of templates in category
        """
        return [
            tpl for tpl in self.templates.values()
            if tpl.category == category
        ]

    def create_template(
        self,
        name: str,
        subject: str,
        body: str,
        category: str = "General",
        variables: Optional[List[str]] = None
    ) -> EmailTemplate:
        """Create a new template.

        Args:
            name: Template name
            subject: Email subject template
            body: Email body template
            category: Template category
            variables: List of variable names

        Returns:
            Created template
        """
        # Generate ID
        template_id = name.lower().replace(" ", "_").replace("/", "_")

        # Check if ID exists
        counter = 1
        original_id = template_id
        while template_id in self.templates:
            template_id = f"{original_id}_{counter}"
            counter += 1

        template = EmailTemplate(
            id=template_id,
            name=name,
            subject=subject,
            body=body,
            category=category,
            variables=variables or [],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        self.templates[template_id] = template
        self._save_templates()

        logger.info(f"Created template: {template_id}")
        return template

    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        category: Optional[str] = None,
        variables: Optional[List[str]] = None
    ) -> Optional[EmailTemplate]:
        """Update an existing template.

        Args:
            template_id: Template ID
            name: New name
            subject: New subject
            body: New body
            category: New category
            variables: New variables

        Returns:
            Updated template or None
        """
        if template_id not in self.templates:
            logger.warning(f"Template not found: {template_id}")
            return None

        template = self.templates[template_id]

        if name is not None:
            template.name = name
        if subject is not None:
            template.subject = subject
        if body is not None:
            template.body = body
        if category is not None:
            template.category = category
        if variables is not None:
            template.variables = variables

        template.updated_at = datetime.now().isoformat()

        self._save_templates()
        logger.info(f"Updated template: {template_id}")

        return template

    def delete_template(self, template_id: str) -> bool:
        """Delete a template.

        Args:
            template_id: Template ID

        Returns:
            True if deleted
        """
        if template_id in self.templates:
            del self.templates[template_id]
            self._save_templates()
            logger.info(f"Deleted template: {template_id}")
            return True

        logger.warning(f"Template not found: {template_id}")
        return False

    def apply_template(
        self,
        template_id: str,
        variables: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, str]]:
        """Apply template with variables.

        Args:
            template_id: Template ID
            variables: Dictionary of variable values

        Returns:
            Dictionary with 'subject' and 'body' or None
        """
        template = self.get_template(template_id)
        if not template:
            return None

        subject = template.subject
        body = template.body

        # Replace variables
        if variables:
            for var, value in variables.items():
                placeholder = f"{{{var}}}"
                subject = subject.replace(placeholder, value)
                body = body.replace(placeholder, value)

        return {
            "subject": subject,
            "body": body
        }

    def get_categories(self) -> List[str]:
        """Get all template categories.

        Returns:
            List of unique categories
        """
        categories = set(tpl.category for tpl in self.templates.values())
        return sorted(list(categories))


# Global template manager instance
_template_manager = None


def get_template_manager() -> TemplateManager:
    """Get global template manager instance.

    Returns:
        TemplateManager instance
    """
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager
