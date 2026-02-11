import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Microsoft Azure AD
    MS_CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
    MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "")
    MS_TENANT_ID = os.getenv("MS_TENANT_ID", "")
    MS_REDIRECT_URI = os.getenv("MS_REDIRECT_URI", "http://localhost:5000/callback")
    MS_AUTHORITY = f"https://login.microsoftonline.com/{MS_TENANT_ID}"
    MS_SCOPES = [
        "User.Read",
        "OnlineMeetings.Read",
        "OnlineMeetingTranscript.Read.All",
        "Chat.Read",
        "CallRecords.Read",
    ]

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    PORT = int(os.getenv("FLASK_PORT", "5000"))

    # Graph API
    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
