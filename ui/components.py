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
            ["Inbox", "Compose", "Search", "Analytics", "Filters", "Templates", "Batch Operations", "Agent Chat", "Settings"],
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


def render_template_selector():
    """Render email template selector.

    Returns:
        Selected template ID or None
    """
    from utils.templates import get_template_manager

    template_manager = get_template_manager()
    templates = template_manager.get_all_templates()

    if not templates:
        st.info("No templates available. Create one below!")
        return None

    st.subheader("📝 Email Templates")

    # Group by category
    categories = template_manager.get_categories()

    # Category filter
    selected_category = st.selectbox(
        "Category",
        ["All"] + categories
    )

    # Filter templates
    if selected_category == "All":
        filtered_templates = templates
    else:
        filtered_templates = template_manager.get_templates_by_category(selected_category)

    if not filtered_templates:
        st.info(f"No templates in category '{selected_category}'")
        return None

    # Template selector
    template_options = {tpl.id: f"{tpl.name} ({tpl.category})" for tpl in filtered_templates}
    selected_id = st.selectbox(
        "Select Template",
        options=list(template_options.keys()),
        format_func=lambda x: template_options[x]
    )

    if selected_id:
        template = template_manager.get_template(selected_id)

        # Preview
        with st.expander("Preview Template"):
            st.markdown(f"**Subject:** {template.subject}")
            st.markdown("**Body:**")
            st.text(template.body)

            if template.variables:
                st.markdown("**Variables:** " + ", ".join([f"`{{{var}}}`" for var in template.variables]))

        # Variable inputs
        if template.variables:
            st.markdown("### Fill in Variables")
            variables = {}

            for var in template.variables:
                variables[var] = st.text_input(
                    f"{var}",
                    key=f"var_{selected_id}_{var}"
                )

            if st.button("Apply Template", type="primary"):
                result = template_manager.apply_template(selected_id, variables)
                return {
                    "template_id": selected_id,
                    "subject": result["subject"],
                    "body": result["body"]
                }

    return None


def render_template_manager():
    """Render template management interface."""
    from utils.templates import get_template_manager

    st.subheader("📚 Template Management")

    template_manager = get_template_manager()

    tab1, tab2, tab3 = st.tabs(["Create", "Edit", "Delete"])

    with tab1:
        st.markdown("### Create New Template")

        with st.form("create_template"):
            name = st.text_input("Template Name")
            category = st.text_input("Category", value="General")
            subject = st.text_input("Subject Template")
            body = st.text_area("Body Template", height=200)
            variables = st.text_input(
                "Variables (comma-separated)",
                placeholder="e.g., 이름, 날짜, 주제"
            )

            if st.form_submit_button("Create Template"):
                if name and subject and body:
                    var_list = [v.strip() for v in variables.split(",") if v.strip()]

                    template = template_manager.create_template(
                        name=name,
                        subject=subject,
                        body=body,
                        category=category,
                        variables=var_list
                    )

                    st.success(f"Template '{name}' created successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields")

    with tab2:
        st.markdown("### Edit Template")

        templates = template_manager.get_all_templates()
        if templates:
            template_options = {tpl.id: tpl.name for tpl in templates}
            selected_id = st.selectbox(
                "Select Template to Edit",
                options=list(template_options.keys()),
                format_func=lambda x: template_options[x],
                key="edit_selector"
            )

            if selected_id:
                template = template_manager.get_template(selected_id)

                with st.form("edit_template"):
                    name = st.text_input("Template Name", value=template.name)
                    category = st.text_input("Category", value=template.category)
                    subject = st.text_input("Subject Template", value=template.subject)
                    body = st.text_area("Body Template", value=template.body, height=200)
                    variables = st.text_input(
                        "Variables (comma-separated)",
                        value=", ".join(template.variables) if template.variables else ""
                    )

                    if st.form_submit_button("Update Template"):
                        var_list = [v.strip() for v in variables.split(",") if v.strip()]

                        template_manager.update_template(
                            template_id=selected_id,
                            name=name,
                            subject=subject,
                            body=body,
                            category=category,
                            variables=var_list
                        )

                        st.success(f"Template updated successfully!")
                        st.rerun()
        else:
            st.info("No templates available to edit")

    with tab3:
        st.markdown("### Delete Template")

        templates = template_manager.get_all_templates()
        if templates:
            template_options = {tpl.id: tpl.name for tpl in templates}
            selected_id = st.selectbox(
                "Select Template to Delete",
                options=list(template_options.keys()),
                format_func=lambda x: template_options[x],
                key="delete_selector"
            )

            if selected_id:
                template = template_manager.get_template(selected_id)

                st.warning(f"Are you sure you want to delete template '{template.name}'?")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Yes, Delete", type="primary"):
                        template_manager.delete_template(selected_id)
                        st.success("Template deleted successfully!")
                        st.rerun()

                with col2:
                    if st.button("Cancel"):
                        st.info("Deletion cancelled")
        else:
            st.info("No templates available to delete")


def render_batch_operations(emails: List[EmailMessage]):
    """Render batch operations interface.

    Args:
        emails: List of emails to operate on
    """
    from utils.batch_operations import BatchActionType

    st.subheader("⚡ Batch Operations")

    if not emails:
        st.info("No emails to perform batch operations on")
        return None

    # Email selection
    st.markdown(f"### Select Emails ({len(emails)} available)")

    # Select all checkbox
    select_all = st.checkbox("Select All")

    # Individual selection
    selected_emails = []

    if select_all:
        selected_emails = emails
        st.info(f"All {len(emails)} emails selected")
    else:
        # Show email list with checkboxes
        for idx, email in enumerate(emails[:20]):  # Limit to 20 for UI performance
            col1, col2 = st.columns([1, 9])

            with col1:
                if st.checkbox("", key=f"batch_select_{idx}_{email.id}"):
                    selected_emails.append(email)

            with col2:
                st.markdown(f"**{email.subject}** from {email.sender}")

        if len(emails) > 20:
            st.info(f"Showing first 20 emails. Use 'Select All' to select all {len(emails)} emails.")

    if not selected_emails:
        st.warning("No emails selected")
        return None

    st.markdown(f"**{len(selected_emails)} email(s) selected**")

    # Action selection
    st.markdown("### Select Action")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📖 Mark as Read", use_container_width=True):
            return {
                "action": BatchActionType.MARK_READ,
                "emails": selected_emails
            }

    with col2:
        if st.button("📬 Mark as Unread", use_container_width=True):
            return {
                "action": BatchActionType.MARK_UNREAD,
                "emails": selected_emails
            }

    with col3:
        if st.button("⭐ Star", use_container_width=True):
            return {
                "action": BatchActionType.STAR,
                "emails": selected_emails
            }

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📂 Archive", use_container_width=True):
            return {
                "action": BatchActionType.ARCHIVE,
                "emails": selected_emails
            }

    with col2:
        if st.button("🗑️ Delete", use_container_width=True):
            st.warning("⚠️ This will delete the selected emails!")
            if st.button("Confirm Delete", type="primary"):
                return {
                    "action": BatchActionType.DELETE,
                    "emails": selected_emails
                }

    return None


def render_analytics_dashboard(emails: List[EmailMessage]):
    """Render email analytics dashboard.

    Args:
        emails: List of emails to analyze
    """
    from utils.analytics import create_analytics

    if not emails:
        st.info("No emails to analyze. Please load emails from Inbox first.")
        return

    st.subheader("📊 Email Analytics")

    analytics = create_analytics(emails)
    stats = analytics.generate_stats()

    # Key Metrics Row
    st.markdown("### Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Emails", stats.total_emails)

    with col2:
        st.metric("Unread", stats.unread_count, delta=f"-{stats.read_rate:.1f}% read")

    with col3:
        st.metric("Starred", stats.starred_count)

    with col4:
        st.metric("Today", stats.today_count)

    st.divider()

    # Time-based Metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("This Week", stats.this_week_count)

    with col2:
        st.metric("This Month", stats.this_month_count)

    with col3:
        st.metric("Avg/Day", f"{stats.average_per_day:.1f}")

    st.divider()

    # Top Senders
    st.markdown("### 👥 Top Senders")

    if stats.top_senders:
        for i, sender_info in enumerate(stats.top_senders[:10], 1):
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.text(f"{i}. {sender_info['email']}")

            with col2:
                st.text(f"{sender_info['count']} emails")

            with col3:
                st.text(f"{sender_info['percentage']}%")
    else:
        st.info("No sender data available")

    st.divider()

    # Busiest Times
    busiest = analytics.get_busiest_times()
    st.markdown("### ⏰ Busiest Times")

    col1, col2, col3 = st.columns(3)

    with col1:
        if busiest["busiest_hour"]:
            st.metric("Busiest Hour",
                     f"{busiest['busiest_hour']['hour']}:00",
                     f"{busiest['busiest_hour']['count']} emails")

    with col2:
        if busiest["busiest_day"]:
            st.metric("Busiest Day",
                     busiest["busiest_day"]["day"],
                     f"{busiest['busiest_day']['count']} emails")

    with col3:
        if busiest["busiest_month"]:
            st.metric("Busiest Month",
                     busiest["busiest_month"]["month"],
                     f"{busiest['busiest_month']['count']} emails")

    st.divider()

    # Productivity Insights
    st.markdown("### 💡 Productivity Insights")

    insights = analytics.get_productivity_insights()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"""
        **Read Rate:** {insights['read_rate']:.1f}%
        **Emails per Day:** {insights['emails_per_day']:.1f}
        **Unread Percentage:** {insights['unread_percentage']:.1f}%
        """)

        st.info(f"💡 **Recommendation:** {insights['recommendation']}")

    with col2:
        # Progress bar for read rate
        st.progress(insights['read_rate'] / 100)
        st.caption(f"Read Rate: {insights['read_rate']:.1f}%")


def render_advanced_filters():
    """Render advanced filtering interface.

    Returns:
        EmailFilter object or None
    """
    from utils.filters import (
        EmailFilter, FilterField, FilterOperator, PresetFilters
    )
    from datetime import datetime, timedelta

    st.subheader("🔍 Advanced Filters")

    # Preset filters
    st.markdown("### Quick Filters")

    col1, col2, col3 = st.columns(3)

    preset_filter = None

    with col1:
        if st.button("📬 Unread + Attachments", use_container_width=True):
            preset_filter = PresetFilters.unread_with_attachments()

    with col2:
        if st.button("⭐ Today's Important", use_container_width=True):
            preset_filter = PresetFilters.today_important()

    with col3:
        days = st.selectbox("Last N Days", [7, 14, 30, 60, 90], index=0)
        if st.button("📅 Apply", use_container_width=True):
            preset_filter = PresetFilters.last_n_days(days)

    if preset_filter:
        return preset_filter

    st.divider()

    # Custom filters
    st.markdown("### Custom Filter Builder")

    if "filter_rules" not in st.session_state:
        st.session_state["filter_rules"] = []

    # Match mode
    match_mode = st.radio(
        "Match Mode",
        ["Match ALL conditions (AND)", "Match ANY condition (OR)"],
        horizontal=True
    )

    # Add rule form
    with st.expander("➕ Add Filter Rule", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            field = st.selectbox(
                "Field",
                options=[f.value for f in FilterField],
                format_func=lambda x: x.replace("_", " ").title()
            )

        with col2:
            # Show relevant operators based on field
            if field in ["is_read", "is_starred", "has_attachment"]:
                operator_options = [FilterOperator.EQUALS.value]
            elif field == "date":
                operator_options = [
                    FilterOperator.GREATER_THAN.value,
                    FilterOperator.LESS_THAN.value,
                    FilterOperator.EQUALS.value
                ]
            else:
                operator_options = [
                    FilterOperator.EQUALS.value,
                    FilterOperator.NOT_EQUALS.value,
                    FilterOperator.CONTAINS.value,
                    FilterOperator.NOT_CONTAINS.value,
                    FilterOperator.STARTS_WITH.value,
                    FilterOperator.ENDS_WITH.value,
                ]

            operator = st.selectbox(
                "Operator",
                options=operator_options,
                format_func=lambda x: x.replace("_", " ").title()
            )

        with col3:
            # Value input based on field type
            if field in ["is_read", "is_starred", "has_attachment"]:
                value = st.selectbox("Value", [True, False])
            elif field == "date":
                value = st.date_input("Value", value=datetime.now() - timedelta(days=7))
                value = datetime.combine(value, datetime.min.time())
            else:
                value = st.text_input("Value", placeholder="Enter value...")

        case_sensitive = st.checkbox("Case Sensitive", value=False)

        if st.button("Add Rule", type="primary"):
            if value:
                st.session_state["filter_rules"].append({
                    "field": field,
                    "operator": operator,
                    "value": value,
                    "case_sensitive": case_sensitive
                })
                st.success("Rule added!")
                st.rerun()

    # Show current rules
    if st.session_state["filter_rules"]:
        st.markdown("### Current Rules")

        for i, rule in enumerate(st.session_state["filter_rules"]):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.text(
                    f"{i+1}. {rule['field']} {rule['operator']} {rule['value']}"
                )

            with col2:
                if st.button("❌", key=f"remove_rule_{i}"):
                    st.session_state["filter_rules"].pop(i)
                    st.rerun()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Apply Filters", type="primary", use_container_width=True):
                # Build filter
                email_filter = EmailFilter()
                email_filter.set_match_mode(match_mode.startswith("Match ALL"))

                for rule in st.session_state["filter_rules"]:
                    email_filter.add_rule(
                        field=FilterField(rule["field"]),
                        operator=FilterOperator(rule["operator"]),
                        value=rule["value"],
                        case_sensitive=rule.get("case_sensitive", False)
                    )

                return email_filter

        with col2:
            if st.button("Clear All Rules", use_container_width=True):
                st.session_state["filter_rules"] = []
                st.rerun()

    else:
        st.info("No filter rules defined. Add rules above to start filtering.")

    return None
