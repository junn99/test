"""Main Streamlit application for Email Assistant Agent."""

import streamlit as st
from loguru import logger
import sys

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("email_assistant.log", rotation="10 MB", level="DEBUG")

from config.settings import settings
from services.gmail_service import GmailService
from agents.email_agent import EmailAssistantWithMemory
from services.base_email import EmailDraft
from ui.components import (
    render_sidebar,
    render_email_card,
    render_email_composer,
    render_chat_interface,
    render_search_interface,
    render_template_selector,
    render_template_manager,
    render_batch_operations,
    render_analytics_dashboard,
    render_advanced_filters,
    show_notification,
)


# Page configuration
st.set_page_config(
    page_title="Email Assistant Agent",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "initialized" not in st.session_state:
        st.session_state["initialized"] = False
        st.session_state["email_service"] = None
        st.session_state["agent"] = None
        st.session_state["chat_history"] = []
        st.session_state["emails"] = []
        st.session_state["stats"] = {"unread": 0, "total": 0, "drafts": 0}
        st.session_state["authenticated"] = False


def authenticate_services():
    """Authenticate email service and initialize agent."""
    if not st.session_state["authenticated"]:
        try:
            with st.spinner("Authenticating with Gmail..."):
                # Initialize email service
                email_service = GmailService()
                email_service.authenticate()
                st.session_state["email_service"] = email_service

                # Initialize agent
                agent = EmailAssistantWithMemory(email_service=email_service)
                st.session_state["agent"] = agent

                st.session_state["authenticated"] = True
                logger.info("Services authenticated successfully")
                show_notification("Successfully authenticated!", "success")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            st.error(f"Authentication failed: {str(e)}")
            st.info("""
            **Setup Instructions:**

            1. **Get Gmail API Credentials:**
               - Go to [Google Cloud Console](https://console.cloud.google.com/)
               - Create a new project or select existing one
               - Enable Gmail API
               - Create OAuth 2.0 credentials
               - Download credentials.json

            2. **Configure Environment:**
               - Copy credentials.json to project root
               - Copy .env.example to .env
               - Add your OpenAI or Anthropic API key to .env

            3. **Restart the application**
            """)
            st.stop()


def render_inbox_page():
    """Render inbox page."""
    st.title("📬 Inbox")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        max_emails = st.number_input("Max Emails", min_value=1, max_value=100, value=20)

    with col2:
        filter_option = st.selectbox(
            "Filter",
            ["All", "Unread Only", "Starred Only"]
        )

    with col3:
        if st.button("Refresh", type="primary"):
            st.session_state["refresh_inbox"] = True

    # Fetch emails
    if st.session_state["refresh_inbox"] or not st.session_state["emails"]:
        try:
            with st.spinner("Fetching emails..."):
                email_service = st.session_state["email_service"]

                unread_only = filter_option == "Unread Only"
                query = "is:starred" if filter_option == "Starred Only" else None

                emails = email_service.get_messages(
                    max_results=max_emails,
                    unread_only=unread_only,
                    query=query
                )

                st.session_state["emails"] = emails
                st.session_state["refresh_inbox"] = False

                # Update stats
                unread_count = sum(1 for email in emails if not email.is_read)
                st.session_state["stats"]["unread"] = unread_count
                st.session_state["stats"]["total"] = len(emails)

                show_notification(f"Fetched {len(emails)} emails", "success")

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            st.error(f"Error fetching emails: {str(e)}")
            return

    # Display emails
    if st.session_state["emails"]:
        st.markdown(f"### {len(st.session_state['emails'])} Email(s)")

        for idx, email in enumerate(st.session_state["emails"]):
            render_email_card(email, idx)

    else:
        st.info("No emails found. Click 'Refresh' to fetch emails.")


def render_compose_page():
    """Render compose email page."""
    st.title("✍️ Compose Email")

    # Check if replying
    reply_to = st.session_state.get("reply_to")

    if reply_to:
        st.info(f"Replying to: {reply_to.subject}")

    # Template selector (optional)
    with st.expander("📝 Use Email Template"):
        template_result = render_template_selector()
        if template_result:
            st.session_state["template_subject"] = template_result["subject"]
            st.session_state["template_body"] = template_result["body"]
            st.success("Template applied! Scroll down to see the composer.")

    # Render composer
    compose_result = render_email_composer(reply_to=reply_to)

    if compose_result:
        action = compose_result["action"]
        email_service = st.session_state["email_service"]
        agent = st.session_state["agent"]

        try:
            if action == "generate":
                # Use AI to generate/improve email
                with st.spinner("Generating email with AI..."):
                    prompt = f"""
                    Generate an email with the following details:
                    - To: {', '.join(compose_result['to'])}
                    - Subject: {compose_result['subject']}
                    - Tone: {compose_result['tone']}
                    - Length: {compose_result['length']}
                    - Current body: {compose_result['body']}
                    """

                    if compose_result['ai_instruction']:
                        prompt += f"\n- Additional instructions: {compose_result['ai_instruction']}"

                    response = agent.run(prompt)
                    st.success("Email generated!")
                    st.markdown("### Generated Email:")
                    st.write(response.get("output", ""))

            elif action == "draft":
                # Save as draft
                with st.spinner("Saving draft..."):
                    draft = EmailDraft(
                        to=compose_result['to'],
                        subject=compose_result['subject'],
                        body=compose_result['body'],
                        cc=compose_result['cc']
                    )

                    draft_id = email_service.create_draft(draft)

                    if draft_id:
                        show_notification(f"Draft saved! ID: {draft_id}", "success")
                    else:
                        show_notification("Failed to save draft", "error")

            elif action == "send":
                # Send email
                st.warning("Are you sure you want to send this email?")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Yes, Send", type="primary"):
                        with st.spinner("Sending email..."):
                            draft = EmailDraft(
                                to=compose_result['to'],
                                subject=compose_result['subject'],
                                body=compose_result['body'],
                                cc=compose_result['cc']
                            )

                            success = email_service.send_message(draft)

                            if success:
                                show_notification("Email sent successfully!", "success")
                                st.session_state["reply_to"] = None
                            else:
                                show_notification("Failed to send email", "error")

                with col2:
                    if st.button("Cancel"):
                        st.info("Email not sent")

        except Exception as e:
            logger.error(f"Error in compose action: {e}")
            st.error(f"Error: {str(e)}")

    # Clear reply state if exists
    if st.button("Clear Form"):
        st.session_state["reply_to"] = None
        st.rerun()


def render_search_page():
    """Render search page."""
    st.title("🔍 Search Emails")

    search_params = render_search_interface()

    if search_params:
        try:
            with st.spinner("Searching..."):
                email_service = st.session_state["email_service"]

                results = email_service.search_messages(
                    query=search_params["query"],
                    max_results=search_params["max_results"]
                )

                st.markdown(f"### Found {len(results)} Email(s)")

                for idx, email in enumerate(results):
                    render_email_card(email, idx)

        except Exception as e:
            logger.error(f"Search error: {e}")
            st.error(f"Search error: {str(e)}")


def render_agent_chat_page():
    """Render agent chat page."""
    st.title("🤖 Chat with Email Assistant")

    st.markdown("""
    Ask me anything about your emails! I can:
    - Check and summarize your emails
    - Search for specific emails
    - Compose email drafts
    - Send emails (with your confirmation)
    - Answer questions about your inbox
    """)

    prompt = render_chat_interface()

    if prompt:
        agent = st.session_state["agent"]

        try:
            with st.spinner("Thinking..."):
                # Get response from agent
                response = agent.run_with_memory(prompt)

                # Add assistant response to chat history
                assistant_message = response.get("output", "Sorry, I couldn't process that.")

                st.session_state["chat_history"].append({
                    "role": "assistant",
                    "content": assistant_message
                })

                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(assistant_message)

        except Exception as e:
            logger.error(f"Agent error: {e}")
            error_message = f"Sorry, I encountered an error: {str(e)}"

            st.session_state["chat_history"].append({
                "role": "assistant",
                "content": error_message
            })

            with st.chat_message("assistant"):
                st.error(error_message)

    # Clear chat button
    if st.button("Clear Chat History"):
        st.session_state["chat_history"] = []
        agent = st.session_state["agent"]
        agent.clear_memory()
        st.rerun()


def render_settings_page():
    """Render settings page."""
    st.title("⚙️ Settings")

    st.header("Application Settings")

    # LLM Settings
    st.subheader("AI Model Settings")

    col1, col2 = st.columns(2)

    with col1:
        llm_provider = st.selectbox(
            "LLM Provider",
            ["openai", "anthropic"],
            index=0 if settings.llm_provider == "openai" else 1
        )

    with col2:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=settings.llm_temperature,
            step=0.1
        )

    # Email Settings
    st.subheader("Email Settings")

    col1, col2 = st.columns(2)

    with col1:
        check_interval = st.number_input(
            "Check Interval (seconds)",
            min_value=30,
            max_value=3600,
            value=settings.check_interval_seconds
        )

    with col2:
        max_fetch = st.number_input(
            "Max Emails per Fetch",
            min_value=10,
            max_value=100,
            value=settings.max_emails_per_fetch
        )

    # Display current configuration
    st.subheader("Current Configuration")

    with st.expander("View Configuration"):
        st.json({
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
            "default_email_provider": settings.default_email_provider,
        })

    # Account Information
    st.subheader("Account Information")

    if st.button("Revoke Authentication"):
        try:
            from utils.auth import GmailAuthenticator
            auth = GmailAuthenticator()
            auth.revoke_credentials()
            st.session_state["authenticated"] = False
            show_notification("Authentication revoked. Please restart the app.", "warning")
        except Exception as e:
            st.error(f"Error revoking credentials: {e}")


def render_templates_page():
    """Render templates management page."""
    st.title("📚 Email Templates")

    render_template_manager()


def render_analytics_page():
    """Render analytics page."""
    st.title("📊 Analytics")

    # Get current emails from session state
    emails = st.session_state.get("emails", [])

    if not emails:
        st.info("No emails loaded. Please go to Inbox and load emails first.")
        return

    render_analytics_dashboard(emails)


def render_filters_page():
    """Render advanced filters page."""
    st.title("🔍 Advanced Filters")

    # Get current emails from session state
    emails = st.session_state.get("emails", [])

    if not emails:
        st.info("No emails loaded. Please go to Inbox and load emails first.")
        return

    # Render filter interface
    email_filter = render_advanced_filters()

    if email_filter:
        try:
            # Apply filter
            with st.spinner("Applying filters..."):
                filtered_emails = email_filter.apply(emails)

                st.success(f"Filter applied! Found {len(filtered_emails)} matching emails.")

                # Store filtered emails
                st.session_state["filtered_emails"] = filtered_emails

                # Display results
                st.markdown(f"### Results ({len(filtered_emails)} emails)")

                for idx, email in enumerate(filtered_emails[:20]):  # Show first 20
                    render_email_card(email, idx)

                if len(filtered_emails) > 20:
                    st.info(f"Showing first 20 of {len(filtered_emails)} filtered emails.")

        except Exception as e:
            logger.error(f"Filter error: {e}")
            st.error(f"Filter error: {str(e)}")


def render_batch_operations_page():
    """Render batch operations page."""
    st.title("⚡ Batch Operations")

    # Get current emails from session state
    emails = st.session_state.get("emails", [])

    if not emails:
        st.info("No emails loaded. Please go to Inbox and load emails first.")
        return

    # Render batch operations interface
    batch_result = render_batch_operations(emails)

    if batch_result:
        from utils.batch_operations import create_batch_operations

        try:
            email_service = st.session_state["email_service"]
            batch_ops = create_batch_operations(email_service)

            # Extract email IDs
            email_ids = [email.id for email in batch_result["emails"]]

            # Execute batch operation
            with st.spinner(f"Executing {batch_result['action'].value}..."):
                result = batch_ops.execute_batch(
                    message_ids=email_ids,
                    action=batch_result["action"]
                )

                # Show results
                st.success(str(result))

                # Show detailed results
                with st.expander("Detailed Results"):
                    st.json(result.to_dict())

                # Refresh inbox
                st.session_state["refresh_inbox"] = True

        except Exception as e:
            logger.error(f"Batch operation error: {e}")
            st.error(f"Batch operation failed: {str(e)}")


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()

    # Authenticate services
    authenticate_services()

    # Render sidebar and get selected page
    page = render_sidebar()

    # Render selected page
    if page == "Inbox":
        render_inbox_page()
    elif page == "Compose":
        render_compose_page()
    elif page == "Search":
        render_search_page()
    elif page == "Analytics":
        render_analytics_page()
    elif page == "Filters":
        render_filters_page()
    elif page == "Templates":
        render_templates_page()
    elif page == "Batch Operations":
        render_batch_operations_page()
    elif page == "Agent Chat":
        render_agent_chat_page()
    elif page == "Settings":
        render_settings_page()


if __name__ == "__main__":
    main()
