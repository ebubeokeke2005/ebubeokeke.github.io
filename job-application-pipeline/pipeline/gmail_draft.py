"""Creates Gmail DRAFTS (never sends) with the tailored resume attached."""
import base64
import mimetypes
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .contacts import Contact


def _build_message(from_email: str, to_email: str, subject: str, body: str, attachment_path: Path) -> dict:
    message = MIMEMultipart()
    message["to"] = to_email
    message["from"] = from_email
    message["subject"] = subject
    message.attach(MIMEText(body))

    mime_type, _ = mimetypes.guess_type(str(attachment_path))
    mime_type = mime_type or "application/pdf"
    maintype, subtype = mime_type.split("/", 1)
    with open(attachment_path, "rb") as attachment_file:
        part = MIMEApplication(attachment_file.read(), _subtype=subtype)
    part.add_header("Content-Disposition", "attachment", filename=attachment_path.name)
    message.attach(part)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


def _personalize_body(your_name: str, contact: Contact, company: str, role: str) -> str:
    greeting_name = contact.name.split()[0] if contact.name and contact.name != "Unknown" else "there"
    return (
        f"Hi {greeting_name},\n\n"
        f"I'm applying for the {role} role at {company} and wanted to reach out "
        f"directly. I've attached a tailored resume — I'd welcome the chance to "
        f"talk about how my background could contribute to your team.\n\n"
        f"Thanks for your time,\n{your_name}"
    )


def create_drafts(
    credentials: Credentials,
    contacts: list[Contact],
    your_name: str,
    your_email: str,
    company: str,
    role: str,
    resume_pdf_path: Path,
) -> list[str]:
    service = build("gmail", "v1", credentials=credentials)
    subject = f"{your_name} — Application for {role} at {company}"

    draft_ids = []
    for contact in contacts:
        if not contact.email or "not_unlocked" in contact.email:
            continue
        body = _personalize_body(your_name, contact, company, role)
        message = _build_message(your_email, contact.email, subject, body, resume_pdf_path)
        draft = service.users().drafts().create(userId="me", body={"message": message}).execute()
        draft_ids.append(draft["id"])

    return draft_ids
