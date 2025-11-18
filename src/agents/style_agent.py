"""Style learning agent for analyzing and replicating user writing style."""
from typing import List, Dict, Any
import json

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from ..tools.notion_tools import NotionToolkit
from ..tools.analysis_tools import ContentAnalyzer
from ..memory.user_profile import UserProfile
from ..utils.config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class StyleLearningAgent:
    """Agent that learns and replicates user's writing style."""

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.anthropic_api_key,
            temperature=0.3  # Lower temperature for analysis
        )
        self.notion = NotionToolkit()
        self.analyzer = ContentAnalyzer()
        self.profile = UserProfile()

    def learn_from_workspace(self, max_pages: int = 20) -> Dict[str, Any]:
        """
        Analyze user's workspace to learn writing style.

        Args:
            max_pages: Maximum number of pages to analyze.

        Returns:
            Dictionary with learned style characteristics.
        """
        logger.info(f"Learning writing style from up to {max_pages} pages")

        # Get recent pages
        all_pages = self.notion.get_all_pages()

        if not all_pages:
            logger.warning("No pages found in workspace")
            return {"error": "No pages found"}

        # Limit to max_pages
        pages_to_analyze = all_pages[:max_pages]

        # Fetch full content for each page
        page_contents = []
        for page_info in pages_to_analyze:
            logger.info(f"Fetching content for: {page_info['title']}")
            page_data = self.notion.get_page_content(page_id=page_info['id'])

            if "error" not in page_data and page_data.get("content"):
                page_contents.append(page_data)

        if not page_contents:
            logger.warning("No valid page content found")
            return {"error": "No valid content found"}

        logger.info(f"Analyzing {len(page_contents)} pages")

        # Analyze patterns
        writing_patterns = self.analyzer.analyze_writing_patterns(page_contents)
        activity_patterns = self.analyzer.analyze_activity_patterns(page_contents)

        # Extract keywords and tags
        all_text = " ".join([
            f"{page.get('title', '')} {page.get('content', '')}"
            for page in page_contents
        ])
        keywords = self.analyzer.extract_keywords(all_text, top_n=30)
        tags = self.analyzer.extract_tags(page_contents)

        # Use Claude to analyze style
        style_analysis = self._analyze_style_with_llm(page_contents[:10])

        # Combine all insights
        learned_style = {
            "analyzed_at": writing_patterns.get("total_pages", 0),
            "writing_patterns": writing_patterns,
            "activity_patterns": activity_patterns,
            "top_keywords": [kw[0] for kw in keywords[:20]],
            "top_tags": list(dict(sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10]).keys()) if tags else [],
            "style_guide": style_analysis,
        }

        # Save to user profile
        self.profile.add_learned_pattern("writing_style_notes", style_analysis.get("summary", ""))
        self.profile.add_learned_pattern("common_keywords", [kw[0] for kw in keywords[:20]])
        self.profile.add_learned_pattern("frequent_tags", list(tags.keys())[:10] if tags else [])

        # Update statistics
        self.profile.update_statistics(total_pages_analyzed=len(page_contents))

        logger.info("Style learning completed")
        return learned_style

    def _analyze_style_with_llm(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use Claude to analyze writing style from sample pages.

        Args:
            pages: List of page dictionaries with content.

        Returns:
            Dictionary with style analysis.
        """
        # Prepare sample texts
        samples = []
        for page in pages[:10]:  # Limit to 10 pages
            title = page.get("title", "")
            content = page.get("content", "")

            if content:
                # Limit content length to avoid token limits
                content_preview = content[:1000]
                samples.append(f"=== {title} ===\n{content_preview}\n")

        combined_samples = "\n\n".join(samples)

        # Create analysis prompt
        prompt = f"""다음은 사용자가 작성한 Notion 문서들의 샘플입니다.
이 문서들을 분석해서 사용자의 글쓰기 스타일을 파악해주세요.

분석할 문서:
{combined_samples}

다음 항목들을 분석해주세요:
1. 문장 구조 (간결한지, 상세한지, 복잡도)
2. 어투 (격식체, 반말, 전문적, 캐주얼 등)
3. 자주 사용하는 표현이나 패턴
4. 문서 구조화 방식 (헤더, 리스트, 번호 등)
5. 이모지 사용 여부
6. 전반적인 톤 (긍정적, 중립적, 분석적 등)

JSON 형식으로 응답해주세요:
{{
    "sentence_structure": "설명",
    "tone": "설명",
    "common_expressions": ["표현1", "표현2"],
    "structure_preference": "설명",
    "emoji_usage": "설명",
    "overall_tone": "설명",
    "summary": "전체 스타일 요약 (1-2문장)"
}}
"""

        try:
            messages = [
                SystemMessage(content="당신은 글쓰기 스타일을 분석하는 전문가입니다."),
                HumanMessage(content=prompt)
            ]

            response = self.llm.invoke(messages)
            content = response.content

            # Try to parse JSON from response
            # Claude might wrap JSON in code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            style_analysis = json.loads(content)
            logger.info("Style analysis completed with LLM")
            return style_analysis

        except Exception as e:
            logger.error(f"Error in LLM style analysis: {e}")
            return {
                "sentence_structure": "분석 실패",
                "tone": "분석 실패",
                "common_expressions": [],
                "structure_preference": "분석 실패",
                "emoji_usage": "분석 실패",
                "overall_tone": "분석 실패",
                "summary": f"스타일 분석 중 오류 발생: {str(e)}"
            }

    def generate_content_with_style(
        self,
        topic: str,
        content_type: str = "note",
        length: str = "medium"
    ) -> str:
        """
        Generate content in the user's learned style.

        Args:
            topic: Topic to write about.
            content_type: Type of content (note, report, summary, etc.).
            length: Desired length (short, medium, long).

        Returns:
            Generated content in user's style.
        """
        # Load learned style
        style_notes = self.profile.profile_data.get("learned_patterns", {}).get("writing_style_notes", "")

        if not style_notes:
            logger.warning("No learned style found, using default")
            style_notes = "Professional and clear writing style."

        # Get user preferences
        report_style = self.profile.get_preference("report_style", "concise")
        language_tone = self.profile.get_preference("language_tone", "professional")
        content_structure = self.profile.get_preference("content_structure", "bullet_points")

        # Create generation prompt
        length_guides = {
            "short": "100-200 단어",
            "medium": "300-500 단어",
            "long": "600-1000 단어"
        }

        prompt = f"""다음 주제에 대해 글을 작성해주세요: {topic}

문서 유형: {content_type}
목표 길이: {length_guides.get(length, "적절한 길이")}

사용자의 글쓰기 스타일:
{style_notes}

추가 선호사항:
- 스타일: {report_style}
- 톤: {language_tone}
- 구조: {content_structure}

위 스타일을 반영해서 자연스럽고 일관성 있게 작성해주세요.
"""

        try:
            messages = [
                SystemMessage(content="당신은 사용자의 글쓰기 스타일을 완벽하게 모방할 수 있는 작가입니다."),
                HumanMessage(content=prompt)
            ]

            response = self.llm.invoke(messages)
            generated_content = response.content

            logger.info(f"Generated content for topic: {topic}")
            return generated_content

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return f"콘텐츠 생성 중 오류 발생: {str(e)}"

    def get_style_summary(self) -> str:
        """
        Get a human-readable summary of the learned style.

        Returns:
            Style summary text.
        """
        style_notes = self.profile.profile_data.get("learned_patterns", {}).get("writing_style_notes", "")

        if not style_notes:
            return "아직 학습된 스타일이 없습니다. 작업공간 분석을 실행해주세요."

        keywords = self.profile.profile_data.get("learned_patterns", {}).get("common_keywords", [])
        tags = self.profile.profile_data.get("learned_patterns", {}).get("frequent_tags", [])

        summary = f"""
📝 학습된 글쓰기 스타일:
{style_notes}

🔑 주요 키워드:
{', '.join(keywords[:10]) if keywords else 'N/A'}

🏷️ 자주 사용하는 태그:
{', '.join(tags[:10]) if tags else 'N/A'}
"""

        return summary.strip()


def create_style_agent() -> StyleLearningAgent:
    """Create a new StyleLearningAgent instance."""
    return StyleLearningAgent()
