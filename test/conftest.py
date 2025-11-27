import os
from models import Base
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from fastapi.testclient import TestClient
from main import app, get_db

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine", dbname="test_db") as container:
        yield container

@pytest.fixture(scope="session")
def db_engine(postgres_container):
    db_url = postgres_container.get_connection_url()
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    yield engine

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    transaction = connection.begin()
    
    try:
        yield session
    finally:
        if transaction.is_active:
                transaction.rollback()
        session.close()
        connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()

@pytest.fixture(scope="session", autouse=True)
def set_test_environment_variables():
    try:
        os.environ["ADMIN_USERNAME"] = "admin"
        os.environ["ADMIN_PASSWORD"] = "secret"
        os.environ["DATABASE_URL"] = "https://example.com"
        os.environ["SUPABASE_URL"] = "https://example.com"
        os.environ["SUPABASE_KEY"] = "secret"
        os.environ["PRODUCTION"] = "false"
        os.environ["RESEND_API_KEY"] = "secret"
        os.environ["OPENAI_API_KEY"] = "secret"
    finally:
        del os.environ["ADMIN_USERNAME"]
        del os.environ["ADMIN_PASSWORD"]
        del os.environ["DATABASE_URL"]
        del os.environ["SUPABASE_URL"]
        del os.environ["SUPABASE_KEY"]
        del os.environ["PRODUCTION"]
        del os.environ["OPENAI_API_KEY"]
        del os.environ["RESEND_API_KEY"]
