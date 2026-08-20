#!/usr/bin/env python3
"""Job application automation pipeline.

Usage:
    python main.py <job_posting_url>
"""
import sys
from pathlib import Path

from pipeline.config import Config, MissingCredential
from pipeline.contacts import find_contacts
from pipeline.gmail_draft import create_drafts
from pipeline.google_auth import get_credentials
from pipeline.pdf import render_pdf
from pipeline.resume import tailor_resume
from pipeline.scraper import scrape_job_posting
from pipeline.sheets_log import log_application

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python main.py <job_posting_url>")
        return 1
    job_url = sys.argv[1]

    try:
        config = Config()
    except MissingCredential as exc:
        print(f"Configuration error: {exc}")
        return 1

    print(f"Scraping job posting: {job_url}")
    posting = scrape_job_posting(job_url)
    print(f"  Company: {posting.company}")
    print(f"  Description: {len(posting.description)} characters")

    print("Tailoring resume with Claude...")
    tailored_docx = tailor_resume(
        master_resume_path=config.master_resume_path,
        job_description=posting.description,
        company=posting.company,
        api_key=config.anthropic_api_key,
        output_path=OUTPUT_DIR / f"resume_{posting.company.replace(' ', '_')}.docx",
    )
    print(f"  Tailored resume: {tailored_docx}")

    print("Rendering PDF with LibreOffice...")
    resume_pdf = render_pdf(tailored_docx)
    print(f"  PDF: {resume_pdf}")

    print(f"Searching Apollo for contacts at {posting.company}...")
    contacts = find_contacts(config.apollo_api_key, posting.company, config.target_role)
    for contact in contacts:
        print(f"  {contact.name} — {contact.title} — {contact.email or 'no email'}")
    if not contacts:
        print("  No contacts found.")

    print("Authenticating with Google...")
    credentials = get_credentials(config.google_oauth_client_file, config.google_token_file)

    print("Creating Gmail drafts (not sending)...")
    draft_ids = create_drafts(
        credentials=credentials,
        contacts=contacts,
        your_name=config.your_name,
        your_email=config.your_email,
        company=posting.company,
        role=config.target_role,
        resume_pdf_path=resume_pdf,
    )
    print(f"  Created {len(draft_ids)} draft(s). Review and send them from Gmail yourself.")

    status = "drafts created" if draft_ids else "contacts missing emails"
    print("Logging application to Google Sheet...")
    log_application(
        credentials=credentials,
        sheet_id=config.google_sheet_id,
        company=posting.company,
        role=config.target_role,
        url=job_url,
        contacts=contacts,
        status=status,
    )
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
