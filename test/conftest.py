import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
from models import Base
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from fastapi.testclient import TestClient
from main import app, get_db

@pytest.fixture(scope="session")
def db_engine():
    load_dotenv()
    test_db_url = os.getenv("TEST_DATABASE_URL")
    print(f"DEBUG: TEST_DATABASE_URL={test_db_url}")
    
    if test_db_url:
        engine = create_engine(test_db_url)
        Base.metadata.create_all(engine)
        yield engine
        # Optionally drop tables after test session if desired, but for now we keep it simple
        # Base.metadata.drop_all(engine) 
    else:
        with PostgresContainer("postgres:16-alpine", dbname="test_db") as container:
            db_url = container.get_connection_url()
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