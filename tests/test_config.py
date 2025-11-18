"""Tests for configuration."""
import pytest
from pathlib import Path


def test_config_imports():
    """Test that config module imports correctly."""
    from src.utils.config import settings

    assert settings is not None
    assert hasattr(settings, "vector_db_path")
    assert hasattr(settings, "data_dir")


def test_data_directories_created():
    """Test that data directories are created."""
    from src.utils.config import settings

    assert settings.data_dir.exists()
    assert settings.profiles_dir.exists()
    assert settings.cache_dir.exists()
