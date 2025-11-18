#!/usr/bin/env python
"""Basic test script to verify core functionality."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from src.utils.config import settings
        print("  ✅ Config import OK")
    except Exception as e:
        print(f"  ❌ Config import FAILED: {e}")
        return False

    try:
        from src.utils.logger import setup_logger
        print("  ✅ Logger import OK")
    except Exception as e:
        print(f"  ❌ Logger import FAILED: {e}")
        return False

    try:
        from src.utils.rate_limiter import notion_rate_limiter
        print("  ✅ Rate limiter import OK")
    except Exception as e:
        print(f"  ❌ Rate limiter import FAILED: {e}")
        return False

    try:
        from src.utils.cache import get_cache
        print("  ✅ Cache import OK")
    except Exception as e:
        print(f"  ❌ Cache import FAILED: {e}")
        return False

    try:
        from src.tools.notion_tools import NotionToolkit
        print("  ✅ Notion tools import OK")
    except Exception as e:
        print(f"  ❌ Notion tools import FAILED: {e}")
        return False

    try:
        from src.tools.analysis_tools import ContentAnalyzer
        print("  ✅ Analysis tools import OK")
    except Exception as e:
        print(f"  ❌ Analysis tools import FAILED: {e}")
        return False

    try:
        from src.memory.user_profile import UserProfile
        print("  ✅ User profile import OK")
    except Exception as e:
        print(f"  ❌ User profile import FAILED: {e}")
        return False

    try:
        from src.rag.vector_store import VectorStoreManager
        print("  ✅ Vector store import OK")
    except Exception as e:
        print(f"  ❌ Vector store import FAILED: {e}")
        return False

    try:
        from src.sync.daily_sync import DailySync
        print("  ✅ Sync import OK")
    except Exception as e:
        print(f"  ❌ Sync import FAILED: {e}")
        return False

    try:
        from src.agents.style_agent import create_style_agent
        print("  ✅ Style agent import OK")
    except Exception as e:
        print(f"  ❌ Style agent import FAILED: {e}")
        return False

    try:
        from src.agents.notion_agent import create_agent
        print("  ✅ Notion agent import OK")
    except Exception as e:
        print(f"  ❌ Notion agent import FAILED: {e}")
        return False

    try:
        from src.agents.multi_agent import create_multi_agent_system
        print("  ✅ Multi-agent import OK")
    except Exception as e:
        print(f"  ❌ Multi-agent import FAILED: {e}")
        return False

    return True


def test_toolkit_creation():
    """Test that toolkits can be created."""
    print("\nTesting toolkit creation...")

    try:
        from src.tools.notion_tools import NotionToolkit
        toolkit = NotionToolkit()
        tools = toolkit.get_tools()
        print(f"  ✅ Notion toolkit created with {len(tools)} tools")

        # Check tool types
        from langchain_core.tools import StructuredTool
        for i, tool in enumerate(tools):
            if not isinstance(tool, StructuredTool):
                print(f"  ❌ Tool {i} is not a StructuredTool: {type(tool)}")
                return False

        print("  ✅ All tools are properly structured")

    except Exception as e:
        print(f"  ❌ Toolkit creation FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    try:
        from src.tools.analysis_tools import ContentAnalyzer
        analyzer = ContentAnalyzer()
        tools = analyzer.get_tools()
        print(f"  ✅ Analysis toolkit created with {len(tools)} tools")

        # Check tool types
        for i, tool in enumerate(tools):
            if not isinstance(tool, StructuredTool):
                print(f"  ❌ Tool {i} is not a StructuredTool: {type(tool)}")
                return False

        print("  ✅ All analysis tools are properly structured")

    except Exception as e:
        print(f"  ❌ Analysis toolkit creation FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_user_profile():
    """Test user profile creation."""
    print("\nTesting user profile...")

    try:
        from src.memory.user_profile import UserProfile
        profile = UserProfile("test_profile")

        # Test basic operations
        profile.set_preference("test_key", "test_value")
        value = profile.get_preference("test_key")

        if value == "test_value":
            print("  ✅ User profile read/write OK")
        else:
            print(f"  ❌ User profile value mismatch: {value}")
            return False

    except Exception as e:
        print(f"  ❌ User profile test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_cache():
    """Test cache operations."""
    print("\nTesting cache...")

    try:
        from src.utils.cache import SimpleCache

        cache = SimpleCache()
        cache.set("test_key", "test_value", ttl=60)
        value = cache.get("test_key")

        if value == "test_value":
            print("  ✅ Cache operations OK")
        else:
            print(f"  ❌ Cache value mismatch: {value}")
            return False

        # Test expiry
        cache.set("expire_key", "value", ttl=-1)
        expired_value = cache.get("expire_key")

        if expired_value is None:
            print("  ✅ Cache expiry OK")
        else:
            print(f"  ❌ Cache expiry failed: {expired_value}")
            return False

    except Exception as e:
        print(f"  ❌ Cache test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Notion Knowledge Agent - Basic Tests")
    print("=" * 60)

    all_passed = True

    # Test imports
    if not test_imports():
        all_passed = False

    # Test toolkit creation
    if not test_toolkit_creation():
        all_passed = False

    # Test user profile
    if not test_user_profile():
        all_passed = False

    # Test cache
    if not test_cache():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nNext steps:")
        print("1. Set up .env file with API keys")
        print("2. Run: streamlit run src/dashboard/streamlit_app.py")
        print("3. Or: python cli.py sync --days 1")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease check the error messages above.")

    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
