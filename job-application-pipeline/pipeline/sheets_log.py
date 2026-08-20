"""Appends a row per application to a Google Sheet."""
from datetime import date

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .contacts import Contact

_RANGE = "A:F"


def log_application(
    credentials: Credentials,
    sheet_id: str,
    company: str,
    role: str,
    url: str,
    contacts: list[Contact],
    status: str,
) -> None:
    service = build("sheets", "v4", credentials=credentials)
    contacts_summary = "; ".join(f"{c.name} ({c.title})" for c in contacts) or "none found"

    row = [str(date.today()), company, role, url, contacts_summary, status]
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=_RANGE,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()
