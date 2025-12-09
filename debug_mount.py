import os
import sys

print(f"Current working directory: {os.getcwd()}")
path = "frontend/build/client/assets"
print(f"Checking path: {path}")
print(f"Exists: {os.path.exists(path)}")

try:
    from main import app
    print("Successfully imported app")
except Exception as e:
    print(f"Failed to import app: {e}")
