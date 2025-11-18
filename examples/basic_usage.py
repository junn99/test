"""Basic usage examples for Notion Knowledge Agent."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.notion_agent import create_agent
from src.sync.daily_sync import run_daily_sync
from src.memory.user_profile import UserProfile


def example_chat():
    """Example: Chat with the agent."""
    print("=== Chat Example ===\n")

    agent = create_agent()

    # Ask a question
    response = agent.chat("최근에 작성한 문서들을 요약해줘")
    print(f"Response: {response}\n")


def example_workspace_analysis():
    """Example: Analyze workspace."""
    print("=== Workspace Analysis Example ===\n")

    agent = create_agent()
    analysis = agent.analyze_workspace()

    print(analysis)
    print()


def example_generate_report():
    """Example: Generate a weekly report."""
    print("=== Report Generation Example ===\n")

    agent = create_agent()
    report = agent.generate_report("weekly")

    print(report)
    print()


def example_sync():
    """Example: Sync Notion content."""
    print("=== Sync Example ===\n")

    # Sync recent changes (last 1 day)
    result = run_daily_sync(days=1)

    print(f"Sync completed!")
    print(f"Pages updated: {result.get('pages_updated', 0)}")
    print(f"Pages failed: {result.get('pages_failed', 0)}")
    print(f"Duration: {result.get('duration_seconds', 0):.2f}s")
    print()


def example_user_profile():
    """Example: Manage user profile."""
    print("=== User Profile Example ===\n")

    profile = UserProfile()

    # Set preferences
    profile.set_preference("report_style", "detailed")
    profile.set_preference("language_tone", "professional")

    # Get summary
    print(profile.get_profile_summary())
    print()


if __name__ == "__main__":
    print("Notion Knowledge Agent - Examples\n")
    print("=" * 50)
    print()

    # Run examples
    try:
        example_user_profile()
        # example_sync()  # Uncomment to run sync
        # example_workspace_analysis()  # Uncomment to run analysis
        # example_generate_report()  # Uncomment to generate report
        # example_chat()  # Uncomment to chat

        print("\n" + "=" * 50)
        print("Examples completed!")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Set up .env file with API keys")
        print("2. Connected Notion integration to your pages")
        print("3. Run initial sync")
