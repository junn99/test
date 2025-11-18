"""LangChain email assistant agent."""

from typing import Optional, List, Dict, Any
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import SystemMessage
from loguru import logger

from config.settings import settings
from agents.tools import get_email_tools
from services.gmail_service import GmailService


class EmailAssistantAgent:
    """Email assistant agent powered by LangChain."""

    def __init__(
        self,
        email_service: Optional[GmailService] = None,
        llm_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """Initialize the email assistant agent.

        Args:
            email_service: Email service instance
            llm_provider: LLM provider ('openai' or 'anthropic')
            model_name: Model name to use
            temperature: LLM temperature
        """
        self.email_service = email_service or GmailService()
        self.llm_provider = llm_provider or settings.llm_provider
        self.model_name = model_name or settings.llm_model
        self.temperature = temperature

        # Initialize LLM
        self.llm = self._initialize_llm()

        # Get tools
        self.tools = get_email_tools(self.email_service)

        # Create agent
        self.agent = self._create_agent()

        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
        )

        logger.info("Email assistant agent initialized successfully")

    def _initialize_llm(self):
        """Initialize the LLM based on provider.

        Returns:
            LLM instance
        """
        if self.llm_provider.lower() == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")

            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=settings.openai_api_key,
            )

        elif self.llm_provider.lower() == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")

            return ChatAnthropic(
                model=self.model_name,
                temperature=self.temperature,
                api_key=settings.anthropic_api_key,
            )

        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    def _create_agent(self):
        """Create the LangChain agent with tools.

        Returns:
            Agent instance
        """
        # Create system prompt
        system_message = """You are an intelligent email assistant that helps users manage their emails.

Your capabilities include:
- Checking and reading emails
- Searching for specific emails
- Composing email drafts
- Sending emails (always confirm with user first!)
- Summarizing email content
- Helping prioritize important emails

Guidelines:
1. Always be helpful, clear, and concise in your responses
2. When checking emails, provide a useful summary
3. Before sending any email, ALWAYS show the user the content and ask for confirmation
4. Use appropriate tools to accomplish tasks
5. If you're unsure, ask clarifying questions
6. Respect user privacy and handle email content with care
7. For sensitive operations like sending emails, be extra careful and always confirm

Current task: Help the user manage their emails efficiently."""

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )

        return agent

    def run(self, query: str, chat_history: Optional[List] = None) -> Dict[str, Any]:
        """Run the agent with a user query.

        Args:
            query: User's query/request
            chat_history: Optional chat history

        Returns:
            Agent response dictionary
        """
        try:
            logger.info(f"Processing query: {query}")

            # Prepare input
            input_data = {
                "input": query,
                "chat_history": chat_history or [],
            }

            # Run agent
            response = self.agent_executor.invoke(input_data)

            logger.info("Query processed successfully")
            return response

        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return {
                "output": f"Sorry, I encountered an error: {str(e)}",
                "error": str(e)
            }

    async def arun(self, query: str, chat_history: Optional[List] = None) -> Dict[str, Any]:
        """Run the agent asynchronously.

        Args:
            query: User's query/request
            chat_history: Optional chat history

        Returns:
            Agent response dictionary
        """
        try:
            logger.info(f"Processing query (async): {query}")

            # Prepare input
            input_data = {
                "input": query,
                "chat_history": chat_history or [],
            }

            # Run agent asynchronously
            response = await self.agent_executor.ainvoke(input_data)

            logger.info("Query processed successfully (async)")
            return response

        except Exception as e:
            logger.error(f"Error running agent (async): {e}")
            return {
                "output": f"Sorry, I encountered an error: {str(e)}",
                "error": str(e)
            }

    def stream(self, query: str, chat_history: Optional[List] = None):
        """Stream agent responses.

        Args:
            query: User's query/request
            chat_history: Optional chat history

        Yields:
            Response chunks
        """
        try:
            logger.info(f"Streaming query: {query}")

            # Prepare input
            input_data = {
                "input": query,
                "chat_history": chat_history or [],
            }

            # Stream agent responses
            for chunk in self.agent_executor.stream(input_data):
                yield chunk

        except Exception as e:
            logger.error(f"Error streaming agent response: {e}")
            yield {"error": str(e)}


class EmailAssistantWithMemory(EmailAssistantAgent):
    """Email assistant agent with conversation memory."""

    def __init__(
        self,
        email_service: Optional[GmailService] = None,
        llm_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """Initialize agent with memory.

        Args:
            email_service: Email service instance
            llm_provider: LLM provider
            model_name: Model name
            temperature: LLM temperature
        """
        super().__init__(
            email_service=email_service,
            llm_provider=llm_provider,
            model_name=model_name,
            temperature=temperature,
        )

        # Add memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )

    def run_with_memory(self, query: str) -> Dict[str, Any]:
        """Run agent with memory.

        Args:
            query: User query

        Returns:
            Agent response
        """
        # Get chat history from memory
        chat_history = self.memory.chat_memory.messages

        # Run agent
        response = self.run(query, chat_history=chat_history)

        # Save to memory
        self.memory.save_context(
            {"input": query},
            {"output": response.get("output", "")}
        )

        return response

    def clear_memory(self):
        """Clear conversation memory."""
        self.memory.clear()
        logger.info("Memory cleared")
