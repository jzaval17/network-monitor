"""Test utilities and fixtures."""

import tempfile
import os
from config import TestingConfig


def get_test_database_path():
    """Get path for test database."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    return path


def cleanup_test_database(path):
    """Clean up test database."""
    if os.path.exists(path):
        os.unlink(path)
