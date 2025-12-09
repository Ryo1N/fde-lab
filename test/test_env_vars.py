import os
import pytest
from dotenv import load_dotenv

load_dotenv()

def test_environment_variables():
    """
    Test that critical environment variables are set.
    """
    required_vars = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    assert not missing_vars, f"Missing environment variables: {', '.join(missing_vars)}"
