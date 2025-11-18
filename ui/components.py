"""Streamlit UI components."""

import streamlit as st
from typing import List, Optional
from datetime import datetime

from services.base_email import EmailMessage


def render_email_card(email: EmailMessage, index: int):
    """Render an email card.

    Args:
        email: EmailMessage object
        index: Email index for unique key
    """
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            # Subject with read/unread indicator
            read_indicator = "📧" if email.is_read else "📬"
            st.markdown(f"### {read_indicator} {email.subject}")

            # From
            st.markdown(f"**From:** {email.sender}")

            # Date
            st.markdown(f"**Date:** {email.date.strftime('%Y-%m-%d %H:%M')}")

        with col2:
            # Star indicator
            if email.is_starred:
                st.markdown("⭐ Starred")

            # Labels
            if email.labels:
                for label in email.labels[:3]:  # Show max 3 labels
                    st.badge(label)

        # Snippet
        if email.snippet:
            st.markdown(f"*{email.snippet}*")

        # Expandable full content
        with st.expander("View Full Email"):
            st.text_area(
                "Body",
                value=email.body,
                height=300,
                key=f"email_body_{index}_{email.id}",
                disabled=True
            )

            # Action buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Mark as Read", key=f"read_{index}_{email.id}"):
                    st.session_state[f"action_{email.id}"] = "mark_read"

            with col2:
                if st.button("Reply", key=f"reply_{index}_{email.id}"):
                    st.session_state[f"action_{email.id}"] = "reply"
                    st.session_state["reply_to"] = email

            with col3:
                if st.button("Delete", key=f"delete_{index}_{email.id}"):
                    st.session_state[f"action_{email.id}"] = "delete"

        st.divider()


def render_email_composer(reply_to: Optional[EmailMessage] = None):
    """Render email composition form.

    Args:
        reply_to: Optional email to reply to
    """
    st.subheader("Compose Email")

    with st.form("email_compose_form"):
        # To field
        to_default = reply_to.sender if reply_to else ""
        to = st.text_input("To (comma-separated)", value=to_default)

        # CC field
        cc = st.text_input("CC (comma-separated, optional)")

        # Subject field
        subject_default = f"Re: {reply_to.subject}" if reply_to else ""
        subject = st.text_input("Subject", value=subject_default)

        # Body field
        body_default = ""
        if reply_to:
            body_default = f"\n\n---\nOn {reply_to.date}, {reply_to.sender} wrote:\n{reply_to.body}"

        body = st.text_area("Body", value=body_default, height=300)

        # AI assistance
        st.markdown("### AI Assistance")
        col1, col2 = st.columns(2)

        with col1:
            tone = st.selectbox(
                "Tone",
                ["Professional", "Casual", "Friendly", "Formal"]
            )

        with col2:
            length = st.selectbox(
                "Length",
                ["Short", "Medium", "Long"]
            )

        ai_instruction = st.text_input(
            "AI Instructions (optional)",
            placeholder="e.g., 'Make it more persuasive' or 'Add a call to action'"
        )

        # Buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            generate_draft = st.form_submit_button("Generate with AI")

        with col2:
            save_draft = st.form_submit_button("Save as Draft")

        with col3:
            send_email = st.form_submit_button("Send Email")

        if generate_draft or save_draft or send_email:
            # Parse recipients
            to_list = [email.strip() for email in to.split(",") if email.strip()]
            cc_list = [email.strip() for email in cc.split(",") if email.strip()] if cc else None

            return {
                "action": "generate" if generate_draft else ("draft" if save_draft else "send"),
                "to": to_list,
                "cc": cc_list,
                "subject": subject,
                "body": body,
                "tone": tone,
                "length": length,
                "ai_instruction": ai_instruction,
            }

    return None


def render_sidebar():
    """Render sidebar with navigation and settings."""
    with st.sidebar:
        st.title("Email Assistant")

        # Navigation
        st.header("Navigation")
        page = st.radio(
            "Go to",
            ["Inbox", "Compose", "Search", "Agent Chat", "Settings"],
            label_visibility="collapsed"
        )

        st.divider()

        # Quick Stats
        st.header("Quick Stats")
        if "stats" in st.session_state:
            stats = st.session_state["stats"]
            st.metric("Unread Emails", stats.get("unread", 0))
            st.metric("Total Emails", stats.get("total", 0))
            st.metric("Drafts", stats.get("drafts", 0))

        st.divider()

        # Quick Actions
        st.header("Quick Actions")

        if st.button("Refresh Inbox", use_container_width=True):
            st.session_state["refresh_inbox"] = True

        if st.button("Check New Mail", use_container_width=True):
            st.session_state["check_new_mail"] = True

        st.divider()

        # Info
        st.caption("Email Assistant Agent v1.0")
        st.caption("Powered by LangChain & Streamlit")

    return page


def render_chat_interface():
    """Render chat interface for agent interaction."""
    st.subheader("Chat with Email Assistant")

    # Chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Display chat history
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask me anything about your emails..."):
        # Add user message
        st.session_state["chat_history"].append({
            "role": "user",
            "content": prompt
        })

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        return prompt

    return None


def render_search_interface():
    """Render search interface."""
    st.subheader("Search Emails")

    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="e.g., from:example@gmail.com subject:meeting"
        )

    with col2:
        max_results = st.number_input(
            "Max Results",
            min_value=1,
            max_value=100,
            value=20
        )

    # Search tips
    with st.expander("Search Tips"):
        st.markdown("""
        **Gmail Search Syntax:**
        - `from:example@gmail.com` - emails from specific sender
        - `to:example@gmail.com` - emails to specific recipient
        - `subject:meeting` - emails with 'meeting' in subject
        - `is:unread` - unread emails
        - `is:starred` - starred emails
        - `has:attachment` - emails with attachments
        - `after:2024/01/01` - emails after specific date
        - `before:2024/12/31` - emails before specific date
        - `label:work` - emails with specific label
        """)

    if st.button("Search", type="primary"):
        return {
            "query": query,
            "max_results": max_results
        }

    return None


def show_notification(message: str, type: str = "info"):
    """Show notification message.

    Args:
        message: Notification message
        type: Type of notification ('info', 'success', 'warning', 'error')
    """
    if type == "success":
        st.success(message)
    elif type == "warning":
        st.warning(message)
    elif type == "error":
        st.error(message)
    else:
        st.info(message)
