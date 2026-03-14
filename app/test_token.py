import urllib.request
import os
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2 import service_account
import google.auth.transport.requests

load_dotenv(Path(__file__).resolve().parent / "env" / ".env")
SERVICE_ACCOUNT_FILE = os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON", "")
print("File:", SERVICE_ACCOUNT_FILE)

cred_path = Path(__file__).resolve().parent / SERVICE_ACCOUNT_FILE
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

credentials = service_account.Credentials.from_service_account_file(
    str(cred_path), scopes=SCOPES
)
req = google.auth.transport.requests.Request()
credentials.refresh(req)
print("Token:", len(credentials.token))
