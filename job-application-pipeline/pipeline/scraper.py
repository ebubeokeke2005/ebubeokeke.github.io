"""Scrapes a job posting URL for the job description text and company name."""
import os
from dataclasses import dataclass

from playwright.sync_api import sync_playwright

_DESCRIPTION_SELECTORS = [
    "[class*='job-description']",
    "[class*='jobDescription']",
    "[data-testid*='jobDescription']",
    "#job-description",
    "article",
    "main",
]

_COMPANY_SELECTORS = [
    "[class*='company-name']",
    "[class*='companyName']",
    "[data-testid*='company']",
    "a[href*='/company/']",
]


@dataclass
class JobPosting:
    url: str
    company: str
    description: str


def _first_matching_text(page, selectors: list[str]) -> str:
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.count() and locator.is_visible():
                text = locator.inner_text().strip()
                if text:
                    return text
        except Exception:
            continue
    return ""


def _guess_company(page) -> str:
    for meta_name in ("og:site_name", "author"):
        content = page.locator(f"meta[property='{meta_name}'], meta[name='{meta_name}']").first
        try:
            if content.count():
                value = (content.get_attribute("content") or "").strip()
                if value:
                    return value
        except Exception:
            continue

    company_text = _first_matching_text(page, _COMPANY_SELECTORS)
    if company_text:
        return company_text

    title = (page.title() or "").strip()
    for sep in (" at ", " - ", " | "):
        if sep in title:
            parts = title.split(sep)
            if len(parts) >= 2:
                return parts[-1].strip()
    return title or "Unknown Company"


def scrape_job_posting(url: str) -> JobPosting:
    with sync_playwright() as playwright:
        # Allows pointing at a pre-installed Chromium binary (e.g. in sandboxed
        # environments where `playwright install` can't fetch a browser).
        executable_path = os.environ.get("PLAYWRIGHT_CHROMIUM_PATH")
        browser = playwright.chromium.launch(headless=True, executable_path=executable_path)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)

        description = _first_matching_text(page, _DESCRIPTION_SELECTORS)
        if not description:
            description = page.locator("body").inner_text().strip()

        company = _guess_company(page)
        browser.close()

    return JobPosting(url=url, company=company, description=description)
