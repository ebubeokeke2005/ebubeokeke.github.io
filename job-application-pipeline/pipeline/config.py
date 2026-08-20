"""Loads and validates configuration from .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class MissingCredential(RuntimeError):
    def __init__(self, var_name: str, how_to_get: str):
        super().__init__(
            f"Missing required environment variable: {var_name}\n{how_to_get}"
        )


def _require(var_name: str, how_to_get: str) -> str:
    value = os.environ.get(var_name, "").strip()
    if not value:
        raise MissingCredential(var_name, how_to_get)
    return value


class Config:
    def __init__(self):
        self.anthropic_api_key = _require(
            "ANTHROPIC_API_KEY",
            "Get one at https://console.anthropic.com -> Settings -> API Keys.",
        )
        self.apollo_api_key = _require(
            "APOLLO_API_KEY",
            "Get one at https://app.apollo.io -> Settings -> Integrations -> API.",
        )
        self.google_oauth_client_file = BASE_DIR / os.environ.get(
            "GOOGLE_OAUTH_CLIENT_FILE", "google_oauth_client.json"
        )
        self.google_token_file = BASE_DIR / os.environ.get(
            "GOOGLE_TOKEN_FILE", "google_token.json"
        )
        self.google_sheet_id = _require(
            "GOOGLE_SHEET_ID",
            "Create a Google Sheet, then copy the ID out of its URL: "
            "https://docs.google.com/spreadsheets/d/<ID>/edit",
        )
        self.target_role = os.environ.get("TARGET_ROLE", "Software Engineer").strip()
        self.your_name = os.environ.get("YOUR_NAME", "").strip()
        self.your_email = os.environ.get("YOUR_EMAIL", "").strip()
        self.master_resume_path = BASE_DIR / os.environ.get(
            "MASTER_RESUME_PATH", "master-resume.docx"
        )

        if not self.google_oauth_client_file.exists():
            raise MissingCredential(
                "GOOGLE_OAUTH_CLIENT_FILE",
                f"Expected an OAuth client JSON at {self.google_oauth_client_file}. "
                "Create one at https://console.cloud.google.com -> APIs & Services -> "
                "Credentials -> Create Credentials -> OAuth client ID (Desktop app), "
                "download it, and save it at that path.",
            )
        if not self.master_resume_path.exists():
            raise MissingCredential(
                "MASTER_RESUME_PATH",
                f"Expected your master resume at {self.master_resume_path}. "
                "Place a master-resume.docx in this folder (or point "
                "MASTER_RESUME_PATH at it).",
            )
