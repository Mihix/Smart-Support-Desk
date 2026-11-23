
import os
import sys
from pathlib import Path

# Add project root to Python import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set test credentials before importing the application
os.environ["TEAM_USERNAME"] = "testadmin"
os.environ["TEAM_PASSWORD"] = "testpassword"

import pytest
from fastapi.testclient import TestClient

from api import main


@pytest.fixture
def test_client(tmp_path, monkeypatch):

    test_database = tmp_path / "test_support.db"

    monkeypatch.setattr(
        main,
        "DATABASE_PATH",
        test_database
    )

    main.create_database()

    with TestClient(main.app) as client:
        yield client


@pytest.fixture
def auth_headers():

    return {
        "auth": ("testadmin", "testpassword")
    }
