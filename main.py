"""Main entry point for Notion Knowledge Agent."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Run the Streamlit dashboard."""
    import streamlit.web.cli as stcli
    from src.dashboard.streamlit_app import main as dashboard_main

    sys.argv = ["streamlit", "run", "src/dashboard/streamlit_app.py"]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
