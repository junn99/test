"""Test setup and basic functionality."""

import sys
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")


def test_imports():
    """Test if all required packages can be imported."""
    logger.info("Testing imports...")

    required_packages = [
        ("streamlit", "Streamlit"),
        ("langchain", "LangChain"),
        ("langchain_openai", "LangChain OpenAI"),
        ("langchain_anthropic", "LangChain Anthropic"),
        ("google.oauth2.credentials", "Google Auth"),
        ("googleapiclient.discovery", "Google API Client"),
        ("pydantic", "Pydantic"),
        ("dotenv", "Python Dotenv"),
    ]

    failed = []

    for package, name in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {name} imported successfully")
        except ImportError as e:
            logger.error(f"✗ Failed to import {name}: {e}")
            failed.append(name)

    return len(failed) == 0


def test_config():
    """Test configuration loading."""
    logger.info("Testing configuration...")

    try:
        from config.settings import settings

        logger.info(f"✓ App Name: {settings.app_name}")
        logger.info(f"✓ App Version: {settings.app_version}")
        logger.info(f"✓ LLM Provider: {settings.llm_provider}")
        logger.info(f"✓ Default Email Provider: {settings.default_email_provider}")

        return True
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False


def test_modules():
    """Test if all custom modules can be imported."""
    logger.info("Testing custom modules...")

    modules = [
        "config.settings",
        "utils.auth",
        "utils.helpers",
        "services.base_email",
        "services.gmail_service",
        "agents.tools",
        "agents.email_agent",
        "ui.components",
    ]

    failed = []

    for module in modules:
        try:
            __import__(module)
            logger.info(f"✓ {module} imported successfully")
        except Exception as e:
            logger.error(f"✗ Failed to import {module}: {e}")
            failed.append(module)

    return len(failed) == 0


def test_api_keys():
    """Test if API keys are configured."""
    logger.info("Testing API keys...")

    from config.settings import settings

    has_llm_key = False

    if settings.openai_api_key:
        logger.info("✓ OpenAI API key configured")
        has_llm_key = True

    if settings.anthropic_api_key:
        logger.info("✓ Anthropic API key configured")
        has_llm_key = True

    if not has_llm_key:
        logger.warning("✗ No LLM API key configured (OpenAI or Anthropic)")
        logger.warning("  Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file")
        return False

    return True


def test_gmail_credentials():
    """Test if Gmail credentials file exists."""
    logger.info("Testing Gmail credentials...")

    import os
    from config.settings import settings

    if os.path.exists(settings.gmail_credentials_file):
        logger.info(f"✓ Gmail credentials file found: {settings.gmail_credentials_file}")
        return True
    else:
        logger.warning(f"✗ Gmail credentials file not found: {settings.gmail_credentials_file}")
        logger.warning("  Please download credentials.json from Google Cloud Console")
        return False


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Email Assistant Agent - Setup Test")
    logger.info("=" * 60)

    tests = [
        ("Package Imports", test_imports),
        ("Configuration", test_config),
        ("Custom Modules", test_modules),
        ("API Keys", test_api_keys),
        ("Gmail Credentials", test_gmail_credentials),
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))

    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)

    all_passed = True

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        logger.info(f"{symbol} {test_name}: {status}")

        if not result:
            all_passed = False

    logger.info("=" * 60)

    if all_passed:
        logger.info("✓ All tests passed! You're ready to run the app.")
        logger.info("\nRun the app with: streamlit run app.py")
    else:
        logger.warning("✗ Some tests failed. Please check the errors above.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
