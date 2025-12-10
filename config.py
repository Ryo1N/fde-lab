from pydantic_settings import BaseSettings
from pydantic import AnyUrl
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: AnyUrl
    SUPABASE_URL: AnyUrl
    SUPABASE_KEY: str
    PRODUCTION: bool
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    RESEND_API_KEY: str
    OPENAI_API_KEY: str
    IS_CI: bool = False
    TEST_DATABASE_URL: Optional[str] = None
    BRAINTRUST_API_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 