"""Streamlit dashboard for Notion Knowledge Agent."""
import streamlit as st
from datetime import datetime
import json

from ..agents.notion_agent import create_agent
from ..sync.daily_sync import DailySync
from ..scheduler.jobs import get_scheduler
from ..memory.user_profile import UserProfile
from ..rag.vector_store import VectorStoreManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


# Page configuration
st.set_page_config(
    page_title="Notion Knowledge Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize Streamlit session state."""
    if "agent" not in st.session_state:
        st.session_state.agent = None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "user_profile" not in st.session_state:
        st.session_state.user_profile = UserProfile()

    if "scheduler" not in st.session_state:
        st.session_state.scheduler = get_scheduler()


def load_agent():
    """Load agent lazily."""
    if st.session_state.agent is None:
        with st.spinner("에이전트 초기화 중..."):
            st.session_state.agent = create_agent()
    return st.session_state.agent


def sidebar():
    """Render sidebar."""
    with st.sidebar:
        st.title("📚 Notion Knowledge Agent")
        st.markdown("---")

        # Navigation
        page = st.radio(
            "메뉴",
            ["🏠 Overview", "💬 Chat", "📊 Analytics", "📝 Reports", "⚙️ Settings", "🔄 Sync"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Profile info
        st.subheader("사용자 프로필")
        profile = st.session_state.user_profile
        stats = profile.profile_data.get("statistics", {})

        st.metric("분석된 페이지", stats.get("total_pages_analyzed", 0))
        st.metric("생성된 보고서", stats.get("reports_generated", 0))

        last_sync = stats.get("last_sync")
        if last_sync:
            st.caption(f"마지막 동기화: {last_sync}")
        else:
            st.caption("동기화 기록 없음")

    return page


def page_overview():
    """Overview page."""
    st.title("🏠 Notion 작업공간 개요")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("총 페이지 수", "0", help="벡터 DB에 저장된 페이지")

    with col2:
        st.metric("최근 업데이트", "0", help="지난 24시간 내 수정")

    with col3:
        st.metric("데이터베이스", "0", help="Notion 데이터베이스 개수")

    st.markdown("---")

    # Quick actions
    st.subheader("빠른 작업")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 작업공간 분석", use_container_width=True):
            agent = load_agent()
            with st.spinner("작업공간 분석 중..."):
                result = agent.analyze_workspace()
                st.success("분석 완료!")
                st.markdown(result)

    with col2:
        if st.button("📝 주간 보고서 생성", use_container_width=True):
            agent = load_agent()
            with st.spinner("보고서 생성 중..."):
                result = agent.generate_report("weekly")
                st.success("보고서 생성 완료!")
                st.markdown(result)

    with col3:
        if st.button("🔄 지금 동기화", use_container_width=True):
            with st.spinner("동기화 중..."):
                sync = DailySync()
                result = sync.sync_recent_changes(days=1)
                st.success(f"동기화 완료! {result.get('pages_updated', 0)}개 페이지 업데이트됨")


def page_chat():
    """Chat interface page."""
    st.title("💬 AI 비서와 대화")

    # Chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("무엇을 도와드릴까요?"):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                agent = load_agent()
                response = agent.chat(prompt)
                st.markdown(response)

        # Add assistant message
        st.session_state.chat_history.append({"role": "assistant", "content": response})


def page_analytics():
    """Analytics page."""
    st.title("📊 작업공간 분석")

    profile = st.session_state.user_profile
    patterns = profile.profile_data.get("learned_patterns", {})

    # Keywords
    st.subheader("자주 사용하는 키워드")
    keywords = patterns.get("common_keywords", [])
    if keywords:
        st.write(", ".join(keywords[:20]))
    else:
        st.info("아직 학습된 키워드가 없습니다. 동기화를 실행해주세요.")

    st.markdown("---")

    # Tags
    st.subheader("자주 사용하는 태그")
    tags = patterns.get("frequent_tags", [])
    if tags:
        st.write(", ".join(tags[:20]))
    else:
        st.info("아직 학습된 태그가 없습니다.")

    st.markdown("---")

    # Writing style
    st.subheader("글쓰기 스타일 분석")
    style_notes = patterns.get("writing_style_notes", "")
    if style_notes:
        st.write(style_notes)
    else:
        st.info("글쓰기 스타일이 아직 분석되지 않았습니다.")


def page_reports():
    """Reports generation page."""
    st.title("📝 보고서 생성")

    col1, col2 = st.columns(2)

    with col1:
        report_type = st.selectbox(
            "보고서 유형",
            ["daily", "weekly", "monthly"],
            format_func=lambda x: {"daily": "일간", "weekly": "주간", "monthly": "월간"}[x]
        )

    with col2:
        report_style = st.selectbox(
            "스타일",
            ["concise", "detailed", "technical"],
            format_func=lambda x: {"concise": "간결", "detailed": "상세", "technical": "기술적"}[x]
        )

    if st.button("보고서 생성", use_container_width=True):
        # Update profile preferences
        profile = st.session_state.user_profile
        profile.set_preference("report_style", report_style)

        # Generate report
        agent = load_agent()
        with st.spinner("보고서 생성 중..."):
            report = agent.generate_report(report_type)

        st.markdown("---")
        st.subheader("생성된 보고서")
        st.markdown(report)

        # Download button
        st.download_button(
            label="보고서 다운로드",
            data=report,
            file_name=f"notion_report_{report_type}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )


def page_settings():
    """Settings page."""
    st.title("⚙️ 설정")

    profile = st.session_state.user_profile
    prefs = profile.profile_data.get("preferences", {})

    st.subheader("보고서 설정")

    col1, col2 = st.columns(2)

    with col1:
        report_style = st.selectbox(
            "보고서 스타일",
            ["concise", "detailed", "technical"],
            index=["concise", "detailed", "technical"].index(prefs.get("report_style", "concise")),
            format_func=lambda x: {"concise": "간결", "detailed": "상세", "technical": "기술적"}[x]
        )

        content_structure = st.selectbox(
            "콘텐츠 구조",
            ["bullet_points", "paragraphs", "mixed"],
            index=["bullet_points", "paragraphs", "mixed"].index(
                prefs.get("content_structure", "bullet_points")
            ),
            format_func=lambda x: {
                "bullet_points": "불릿 포인트",
                "paragraphs": "문단",
                "mixed": "혼합"
            }[x]
        )

    with col2:
        report_frequency = st.selectbox(
            "보고서 빈도",
            ["daily", "weekly", "monthly"],
            index=["daily", "weekly", "monthly"].index(prefs.get("report_frequency", "weekly")),
            format_func=lambda x: {"daily": "일간", "weekly": "주간", "monthly": "월간"}[x]
        )

        language_tone = st.selectbox(
            "언어 톤",
            ["professional", "casual", "academic"],
            index=["professional", "casual", "academic"].index(
                prefs.get("language_tone", "professional")
            ),
            format_func=lambda x: {
                "professional": "전문적",
                "casual": "캐주얼",
                "academic": "학술적"
            }[x]
        )

    if st.button("설정 저장", use_container_width=True):
        profile.set_preference("report_style", report_style)
        profile.set_preference("content_structure", content_structure)
        profile.set_preference("report_frequency", report_frequency)
        profile.set_preference("language_tone", language_tone)
        st.success("설정이 저장되었습니다!")

    st.markdown("---")

    st.subheader("프로필 정보")
    st.json(profile.profile_data)


def page_sync():
    """Sync management page."""
    st.title("🔄 동기화 관리")

    st.subheader("수동 동기화")

    col1, col2 = st.columns(2)

    with col1:
        days = st.number_input("최근 며칠", min_value=1, max_value=30, value=1)

    with col2:
        st.write("")  # Spacing

    col1, col2 = st.columns(2)

    with col1:
        if st.button("증분 동기화 실행", use_container_width=True):
            with st.spinner(f"최근 {days}일 동기화 중..."):
                sync = DailySync()
                result = sync.sync_recent_changes(days=days)

                if "error" in result:
                    st.error(f"동기화 실패: {result['error']}")
                else:
                    st.success("동기화 완료!")
                    st.json(result)

    with col2:
        if st.button("전체 동기화 실행", use_container_width=True, type="secondary"):
            st.warning("전체 동기화는 시간이 오래 걸릴 수 있습니다.")
            if st.button("정말 실행하시겠습니까?"):
                with st.spinner("전체 작업공간 동기화 중..."):
                    sync = DailySync()
                    result = sync.full_sync()

                    if "error" in result:
                        st.error(f"동기화 실패: {result['error']}")
                    else:
                        st.success("전체 동기화 완료!")
                        st.json(result)

    st.markdown("---")

    st.subheader("자동 동기화 스케줄")

    scheduler = st.session_state.scheduler

    if not scheduler.is_running:
        if st.button("스케줄러 시작", use_container_width=True):
            scheduler.start()
            st.success("스케줄러가 시작되었습니다!")
            st.rerun()
    else:
        st.success("스케줄러가 실행 중입니다.")

        jobs = scheduler.list_jobs()
        if jobs:
            st.subheader("예약된 작업")
            for job in jobs:
                st.write(f"- **{job['name']}**: 다음 실행 {job['next_run']}")

        if st.button("스케줄러 중지", use_container_width=True, type="secondary"):
            scheduler.stop()
            st.warning("스케줄러가 중지되었습니다.")
            st.rerun()


def main():
    """Main application."""
    init_session_state()

    page = sidebar()

    # Route to pages
    if page == "🏠 Overview":
        page_overview()
    elif page == "💬 Chat":
        page_chat()
    elif page == "📊 Analytics":
        page_analytics()
    elif page == "📝 Reports":
        page_reports()
    elif page == "⚙️ Settings":
        page_settings()
    elif page == "🔄 Sync":
        page_sync()


if __name__ == "__main__":
    main()
