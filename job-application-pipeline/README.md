# Job Application Automation Pipeline

Given a job posting URL, this pipeline scrapes the description, tailors your
resume with Claude, renders a PDF, finds contacts at the company via Apollo,
drafts (never sends) personalized emails in Gmail, and logs the application
to a Google Sheet.

```
python main.py "https://example.com/careers/some-job"
```

## Setup

```
cd job-application-pipeline
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

You'll also need [LibreOffice](https://www.libreoffice.org/) installed
(`soffice` on PATH) for step 4 below — `apt install libreoffice` on
Debian/Ubuntu, `brew install --cask libreoffice` on macOS.

Copy `.env.example` to `.env` and fill it in as you collect the credentials
below. `.env` is gitignored — never commit it.

```
cp .env.example .env
```

Put your master resume at `master-resume.docx` in this folder (or point
`MASTER_RESUME_PATH` in `.env` elsewhere). Bulleted achievements should use a
Word "List Bullet"-style paragraph style — that's how the resume module
finds the bullets it's allowed to rephrase/reorder.

## Getting each credential

### 1. Anthropic API key (resume tailoring)

1. Go to [console.anthropic.com](https://console.anthropic.com) and sign in.
2. Settings → API Keys → Create Key.
3. Paste it into `.env` as `ANTHROPIC_API_KEY`.

### 2. Apollo.io API key (contact finding)

1. Sign up / log in at [app.apollo.io](https://app.apollo.io) (a free plan
   works but limits monthly credits and how many emails you can unlock).
2. Settings → Integrations → API → copy your API key.
3. Paste it into `.env` as `APOLLO_API_KEY`.
4. Note: Apollo often returns a locked placeholder
   (`email_not_unlocked@domain.com`) instead of a real email unless your
   plan includes email credits — the pipeline skips drafting for any
   contact without a usable email.

### 3. Google OAuth client (Gmail drafts + Sheets logging)

Both Gmail and Sheets access go through one OAuth client.

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and
   create (or select) a project.
2. APIs & Services → Library → enable **Gmail API** and **Google Sheets
   API**.
3. APIs & Services → OAuth consent screen → set it up as "External" with
   yourself as a test user (no verification needed for personal use).
4. APIs & Services → Credentials → Create Credentials → OAuth client ID →
   Application type: **Desktop app**.
5. Download the resulting JSON and save it as
   `google_oauth_client.json` in this folder (matches
   `GOOGLE_OAUTH_CLIENT_FILE` in `.env`).
6. The first time you run `main.py`, a browser window opens for you to sign
   in and approve access; the resulting token is cached in
   `google_token.json` so you won't be prompted again.

### 4. Google Sheet to log applications to

1. Create a blank Google Sheet.
2. Copy its ID out of the URL: `https://docs.google.com/spreadsheets/d/<ID>/edit`.
3. Paste it into `.env` as `GOOGLE_SHEET_ID`.
4. Make sure the Google account you authorize in step 3 has edit access to
   this sheet (it does by default if you created it with that account).

### 5. A couple of your own settings

- `TARGET_ROLE` — the role title you're applying for; used both to search
  Apollo for a matching hiring manager and to personalize outreach emails.
- `YOUR_NAME` / `YOUR_EMAIL` — used as the email "from" name and signature.

## What each module does

- `pipeline/scraper.py` — Playwright pulls the job description text and
  company name from the posting URL.
- `pipeline/resume.py` — sends your master resume's existing bullets (by
  section) and the job description to Claude, which may only rephrase and
  reorder them — never invent metrics or experience — and echoes the JD's
  action verbs where it's accurate to do so. It also picks up to 3 verbatim,
  metric-bearing bullets and writes a short "why I'm a fit" paragraph
  grounded only in your existing experience, for use in outreach emails.
- `pipeline/pdf.py` — converts the tailored `.docx` to PDF via headless
  LibreOffice.
- `pipeline/contacts.py` — searches Apollo for a recruiter, a hiring manager
  for `TARGET_ROLE`, and a department head at the company.
- `pipeline/gmail_draft.py` — creates a Gmail **draft** per contact using the
  highlights and fit paragraph from `resume.py` (subject: `<role> application
  - <your name>`), with the tailored PDF attached. Nothing is ever sent
  automatically — review and send from Gmail yourself.
- `pipeline/sheets_log.py` — appends a row (date, company, role, URL,
  contacts found, status) to your tracking sheet.

## Notes / limitations

- Job board markup varies a lot; `scraper.py` uses a handful of common
  selectors and falls back to the page's visible text, so double-check the
  scraped description looks right before proceeding on a new site.
- The resume module rewrites text in place inside your original `.docx`
  structure to preserve formatting; wild custom formatting on individual
  runs (multiple colors/fonts within one bullet) may not be perfectly
  preserved.
