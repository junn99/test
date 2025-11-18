"""Multi-agent collaboration system using LangGraph."""
from typing import TypedDict, Annotated, Literal, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator
import json

from ..tools.notion_tools import NotionToolkit
from ..tools.analysis_tools import ContentAnalyzer
from ..rag.retriever import create_retriever
from ..memory.user_profile import UserProfile
from ..utils.config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class AgentState(TypedDict):
    """Shared state for multi-agent system."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_query: str
    task_type: str  # analyze, write, report, search
    context: str
    analysis_result: dict
    draft_content: str
    final_content: str
    next_agent: str


class SupervisorAgent:
    """Supervisor that coordinates other agents."""

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.anthropic_api_key,
            temperature=0
        )

    def route_task(self, state: AgentState) -> Literal["analyzer", "writer", "editor", "end"]:
        """
        Determine which agent should handle the task next.

        Args:
            state: Current agent state.

        Returns:
            Name of next agent to invoke.
        """
        user_query = state.get("user_query", "")
        task_type = state.get("task_type", "")

        # If task type is already determined
        if task_type:
            if task_type == "analyze":
                return "analyzer"
            elif task_type == "write":
                return "writer"
            elif task_type == "report":
                # Report needs analysis first, then writing
                if not state.get("analysis_result"):
                    return "analyzer"
                elif not state.get("draft_content"):
                    return "writer"
                else:
                    return "editor"

        # Use LLM to determine task type
        prompt = f"""사용자 요청을 분석해서 어떤 에이전트가 처리해야 할지 결정해주세요.

사용자 요청: {user_query}

가능한 에이전트:
- analyzer: 데이터 분석, 패턴 발견, 통계 생성
- writer: 새로운 콘텐츠 작성, 문서 생성
- editor: 기존 콘텐츠 수정, 스타일 적용
- end: 이미 완료되었거나 추가 작업 불필요

JSON 형식으로 응답:
{{"next_agent": "agent_name", "reason": "이유"}}
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content

            # Parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            next_agent = result.get("next_agent", "end")

            logger.info(f"Supervisor routed to: {next_agent} - {result.get('reason', '')}")
            return next_agent

        except Exception as e:
            logger.error(f"Error in supervisor routing: {e}")
            return "end"


class AnalyzerAgent:
    """Agent specialized in data analysis."""

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.anthropic_api_key,
            temperature=0.3
        )
        self.analyzer = ContentAnalyzer()
        self.notion = NotionToolkit()

    def analyze(self, state: AgentState) -> AgentState:
        """
        Perform analysis based on user query.

        Args:
            state: Current state.

        Returns:
            Updated state with analysis results.
        """
        logger.info("Analyzer agent working...")

        user_query = state.get("user_query", "")

        # Get recent pages for analysis
        recent_pages = self.notion.get_recently_edited_pages(days=7)

        # Fetch full content
        page_contents = []
        for page_info in recent_pages[:10]:  # Limit to 10 pages
            page_data = self.notion.get_page_content(page_id=page_info['id'])
            if "error" not in page_data and page_data.get("content"):
                page_contents.append(page_data)

        if not page_contents:
            state["analysis_result"] = {"error": "No content to analyze"}
            return state

        # Perform various analyses
        writing_patterns = self.analyzer.analyze_writing_patterns(page_contents)
        activity_patterns = self.analyzer.analyze_activity_patterns(page_contents)

        all_text = " ".join([
            f"{page.get('title', '')} {page.get('content', '')}"
            for page in page_contents
        ])
        keywords = self.analyzer.extract_keywords(all_text, top_n=20)
        insights = self.analyzer.generate_insights(page_contents)

        # Combine analysis
        analysis_result = {
            "total_pages_analyzed": len(page_contents),
            "writing_patterns": writing_patterns,
            "activity_patterns": activity_patterns,
            "top_keywords": [kw[0] for kw in keywords],
            "insights": insights,
        }

        state["analysis_result"] = analysis_result

        # Create summary message
        summary = f"""
분석 완료!

📊 분석 결과:
- 분석 페이지: {len(page_contents)}개
- 평균 단어 수: {writing_patterns.get('avg_words_per_page', 0):.0f}
- 가장 활발한 시간: {activity_patterns.get('most_active_hour', 'N/A')}

🔑 주요 키워드:
{', '.join([kw[0] for kw in keywords[:10]])}

💡 인사이트:
{chr(10).join([f"- {insight}" for insight in insights])}
"""

        state["messages"] = [AIMessage(content=summary)]
        state["next_agent"] = "end"

        logger.info("Analysis completed")
        return state


class WriterAgent:
    """Agent specialized in content generation."""

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.anthropic_api_key,
            temperature=0.7
        )
        self.profile = UserProfile()

    def write(self, state: AgentState) -> AgentState:
        """
        Generate content based on requirements.

        Args:
            state: Current state.

        Returns:
            Updated state with generated content.
        """
        logger.info("Writer agent working...")

        user_query = state.get("user_query", "")
        analysis_result = state.get("analysis_result", {})
        context = state.get("context", "")

        # Get user preferences
        report_style = self.profile.get_preference("report_style", "concise")
        language_tone = self.profile.get_preference("language_tone", "professional")
        content_structure = self.profile.get_preference("content_structure", "bullet_points")

        # Build writing prompt
        prompt = f"""다음 요청에 따라 콘텐츠를 작성해주세요:

사용자 요청: {user_query}

사용자 선호사항:
- 스타일: {report_style}
- 톤: {language_tone}
- 구조: {content_structure}
"""

        if analysis_result:
            prompt += f"""

분석 데이터:
{json.dumps(analysis_result, ensure_ascii=False, indent=2)}
"""

        if context:
            prompt += f"""

참고 컨텍스트:
{context}
"""

        prompt += """

위 정보를 바탕으로 사용자의 스타일과 선호에 맞게 콘텐츠를 작성해주세요.
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="당신은 전문 작가입니다. 사용자의 스타일과 요구사항에 맞춰 고품질 콘텐츠를 작성합니다."),
                HumanMessage(content=prompt)
            ])

            draft_content = response.content
            state["draft_content"] = draft_content
            state["next_agent"] = "editor"

            logger.info("Draft content generated")

        except Exception as e:
            logger.error(f"Error in writer agent: {e}")
            state["draft_content"] = f"콘텐츠 생성 중 오류 발생: {str(e)}"
            state["next_agent"] = "end"

        return state


class EditorAgent:
    """Agent specialized in editing and style refinement."""

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.anthropic_api_key,
            temperature=0.3
        )
        self.profile = UserProfile()

    def edit(self, state: AgentState) -> AgentState:
        """
        Edit and refine content.

        Args:
            state: Current state.

        Returns:
            Updated state with final content.
        """
        logger.info("Editor agent working...")

        draft_content = state.get("draft_content", "")

        if not draft_content:
            logger.warning("No draft content to edit")
            state["final_content"] = "편집할 초안이 없습니다."
            state["next_agent"] = "end"
            return state

        # Get learned style
        style_notes = self.profile.profile_data.get("learned_patterns", {}).get("writing_style_notes", "")

        prompt = f"""다음 초안을 검토하고 개선해주세요:

초안:
{draft_content}

검토 항목:
1. 문법 및 맞춤법
2. 논리적 흐름
3. 명확성과 간결성
4. 사용자 스타일 반영
"""

        if style_notes:
            prompt += f"""

사용자의 글쓰기 스타일:
{style_notes}

이 스타일에 맞게 조정해주세요.
"""

        prompt += """

최종 개선된 버전만 출력해주세요.
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="당신은 전문 에디터입니다. 콘텐츠를 검토하고 개선합니다."),
                HumanMessage(content=prompt)
            ])

            final_content = response.content
            state["final_content"] = final_content
            state["messages"] = [AIMessage(content=final_content)]
            state["next_agent"] = "end"

            logger.info("Content editing completed")

        except Exception as e:
            logger.error(f"Error in editor agent: {e}")
            state["final_content"] = draft_content  # Fall back to draft
            state["next_agent"] = "end"

        return state


class MultiAgentSystem:
    """Orchestrates multiple specialized agents."""

    def __init__(self):
        self.supervisor = SupervisorAgent()
        self.analyzer = AnalyzerAgent()
        self.writer = WriterAgent()
        self.editor = EditorAgent()
        self.retriever = create_retriever(k=5)

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the multi-agent workflow graph."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("analyzer", self._analyzer_node)
        workflow.add_node("writer", self._writer_node)
        workflow.add_node("editor", self._editor_node)

        # Set entry point
        workflow.set_entry_point("supervisor")

        # Add conditional edges from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            lambda state: state.get("next_agent", "end"),
            {
                "analyzer": "analyzer",
                "writer": "writer",
                "editor": "editor",
                "end": END
            }
        )

        # After each agent, return to supervisor for next decision
        workflow.add_edge("analyzer", "supervisor")
        workflow.add_edge("writer", "supervisor")
        workflow.add_edge("editor", END)

        return workflow.compile()

    def _supervisor_node(self, state: AgentState) -> AgentState:
        """Supervisor decision node."""
        next_agent = self.supervisor.route_task(state)
        state["next_agent"] = next_agent
        return state

    def _analyzer_node(self, state: AgentState) -> AgentState:
        """Analyzer agent node."""
        return self.analyzer.analyze(state)

    def _writer_node(self, state: AgentState) -> AgentState:
        """Writer agent node."""
        return self.writer.write(state)

    def _editor_node(self, state: AgentState) -> AgentState:
        """Editor agent node."""
        return self.editor.edit(state)

    def process(self, query: str, task_type: str = "") -> str:
        """
        Process a user query through the multi-agent system.

        Args:
            query: User query.
            task_type: Optional task type hint (analyze, write, report).

        Returns:
            Final response.
        """
        logger.info(f"Multi-agent system processing: {query}")

        # Retrieve context
        docs = self.retriever.invoke(query)
        context = "\n\n".join([doc.page_content for doc in docs])

        initial_state = {
            "messages": [HumanMessage(content=query)],
            "user_query": query,
            "task_type": task_type,
            "context": context,
            "analysis_result": {},
            "draft_content": "",
            "final_content": "",
            "next_agent": ""
        }

        # Run the graph
        result = self.graph.invoke(initial_state)

        # Extract final response
        if result.get("final_content"):
            response = result["final_content"]
        elif result.get("messages"):
            last_message = result["messages"][-1]
            response = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            response = "처리를 완료했지만 결과를 생성하지 못했습니다."

        logger.info("Multi-agent processing completed")
        return response


def create_multi_agent_system() -> MultiAgentSystem:
    """Create a new multi-agent system instance."""
    return MultiAgentSystem()
