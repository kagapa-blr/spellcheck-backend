from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

os.environ["TESTING"] = "true"

APP_FILE = ROOT_DIR / "app.py"

spec = importlib.util.spec_from_file_location(
    "spellcheck_main",
    APP_FILE,
)

application = importlib.util.module_from_spec(spec)
spec.loader.exec_module(application)


@pytest.fixture(scope="session")
def client():
    with TestClient(application.app) as test_client:
        yield test_client
