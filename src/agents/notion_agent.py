"""Main LangGraph agent for Notion knowledge management."""
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator

from ..tools.notion_tools import NotionToolkit
from ..rag.retriever import create_retriever
from ..memory.user_profile import UserProfile
from ..utils.config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_query: str
    context: str
    retrieved_docs: list
    response: str


class NotionKnowledgeAgent:
    """Main agent for Notion knowledge management using LangGraph."""

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.anthropic_api_key,
            temperature=0.7
        )
        self.notion_toolkit = NotionToolkit()
        self.retriever = create_retriever(k=5)
        self.user_profile = UserProfile()

        # Create tools
        self.tools = self.notion_toolkit.get_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Build graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("retrieve", self._retrieve_context)
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(self.tools))

        # Add edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")

        return workflow.compile()

    def _retrieve_context(self, state: AgentState) -> AgentState:
        """Retrieve relevant context from vector store."""
        logger.info("Retrieving context from vector store")

        query = state.get("user_query", "")
        if not query:
            # Extract from messages
            if state.get("messages"):
                last_message = state["messages"][-1]
                if isinstance(last_message, HumanMessage):
                    query = last_message.content

        if query:
            docs = self.retriever.invoke(query)
            state["retrieved_docs"] = docs
            state["context"] = "\n\n".join([doc.page_content for doc in docs])
            logger.info(f"Retrieved {len(docs)} relevant documents")
        else:
            state["context"] = ""
            state["retrieved_docs"] = []

        return state

    def _agent_node(self, state: AgentState) -> AgentState:
        """Main agent reasoning node."""
        logger.info("Agent processing query")

        # Build context-aware prompt
        messages = list(state.get("messages", []))

        # Add system message with context and profile
        system_context = self._build_system_context(state)

        if messages and isinstance(messages[0], HumanMessage):
            # Enhance first message with context
            enhanced_content = f"{system_context}\n\nUser Query: {messages[0].content}"
            messages[0] = HumanMessage(content=enhanced_content)

        # Invoke LLM with tools
        response = self.llm_with_tools.invoke(messages)
        state["messages"] = [response]

        return state

    def _build_system_context(self, state: AgentState) -> str:
        """Build system context with retrieved docs and user profile."""
        context_parts = [
            "You are a Notion knowledge management assistant.",
            "You help users manage, analyze, and generate content for their Notion workspace.",
            "",
            "User Profile:",
            self.user_profile.get_profile_summary(),
        ]

        if state.get("context"):
            context_parts.extend([
                "",
                "Relevant Context from Notion:",
                state["context"]
            ])

        return "\n".join(context_parts)

    def _should_continue(self, state: AgentState):
        """Determine if agent should continue or end."""
        messages = state.get("messages", [])
        if not messages:
            return "end"

        last_message = messages[-1]

        # Check if there are tool calls
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"

        return "end"

    def chat(self, query: str) -> str:
        """
        Chat with the agent.

        Args:
            query: User query.

        Returns:
            Agent response.
        """
        logger.info(f"User query: {query}")

        initial_state = {
            "messages": [HumanMessage(content=query)],
            "user_query": query,
            "context": "",
            "retrieved_docs": [],
            "response": ""
        }

        # Run the graph
        result = self.graph.invoke(initial_state)

        # Extract response
        if result.get("messages"):
            last_message = result["messages"][-1]
            if isinstance(last_message, AIMessage):
                response = last_message.content
            else:
                response = str(last_message)
        else:
            response = "I apologize, but I couldn't generate a response."

        logger.info(f"Agent response: {response[:100]}...")
        return response

    def analyze_workspace(self) -> str:
        """
        Analyze the entire Notion workspace.

        Returns:
            Analysis summary.
        """
        query = """
        Analyze my Notion workspace:
        1. How many pages do I have?
        2. What are the main topics or categories?
        3. What patterns do you notice in my content?
        4. What are my most frequently used keywords or tags?

        Provide a comprehensive summary.
        """
        return self.chat(query)

    def generate_report(self, report_type: str = "weekly") -> str:
        """
        Generate a report based on user preferences.

        Args:
            report_type: Type of report (daily, weekly, monthly).

        Returns:
            Generated report.
        """
        style = self.user_profile.get_preference("report_style", "concise")
        structure = self.user_profile.get_preference("content_structure", "bullet_points")

        query = f"""
        Generate a {report_type} report of my Notion workspace activity:
        - Style: {style}
        - Structure: {structure}
        - Include: recent changes, completed tasks, upcoming items
        - Highlight: important updates and insights

        Format the report according to my preferences.
        """

        report = self.chat(query)

        # Update statistics
        stats = self.user_profile.profile_data.get("statistics", {})
        stats["reports_generated"] = stats.get("reports_generated", 0) + 1
        self.user_profile.update_statistics(**stats)

        return report


def create_agent() -> NotionKnowledgeAgent:
    """Create a new NotionKnowledgeAgent instance."""
    return NotionKnowledgeAgent()
