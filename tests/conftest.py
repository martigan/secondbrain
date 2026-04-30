from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["APP_DEBUG"] = "false"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"

from src.app import create_app

# Ensure models are imported and registered
from src.domain.models import task, user  # noqa: F401
from src.extensions import db


@pytest.fixture(scope="session")
def app() -> Flask:
    app = create_app()
    app.config.update(TESTING=True)
    return app


@pytest.fixture(autouse=True)
def db_schema(app: Flask) -> Iterator[None]:
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()
