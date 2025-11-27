from sqlalchemy import create_engine
from config import settings
from sqlalchemy.orm import sessionmaker
from config import settings

engine = create_engine(str(settings.DATABASE_URL), echo=not settings.PRODUCTION)

def get_db_session():
  return sessionmaker(bind=engine)()

def get_db():
  db = sessionmaker(bind=engine)()
  try:
      yield db
  finally:
      db.close()


