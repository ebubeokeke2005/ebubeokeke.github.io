"""Finds relevant contacts at a company via the Apollo.io People Search API."""
from dataclasses import dataclass

import requests

_APOLLO_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/search"


@dataclass
class Contact:
    name: str
    title: str
    email: str
    linkedin_url: str


def _search(api_key: str, company: str, titles: list[str], per_page: int) -> list[dict]:
    response = requests.post(
        _APOLLO_SEARCH_URL,
        headers={"Content-Type": "application/json", "X-Api-Key": api_key},
        json={
            "q_organization_name": company,
            "person_titles": titles,
            "page": 1,
            "per_page": per_page,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("people", [])


def find_contacts(api_key: str, company: str, target_role: str) -> list[Contact]:
    """Looks for a recruiter, a hiring manager for target_role, and a department head."""
    title_groups = [
        ["Recruiter", "Technical Recruiter", "Talent Acquisition"],
        [f"{target_role} Manager", "Hiring Manager", "Engineering Manager"],
        ["Head of Engineering", "Director of Engineering", "VP of Engineering"],
    ]

    seen_ids = set()
    contacts: list[Contact] = []
    for titles in title_groups:
        people = _search(api_key, company, titles, per_page=2)
        for person in people:
            person_id = person.get("id")
            if not person_id or person_id in seen_ids:
                continue
            seen_ids.add(person_id)
            contacts.append(
                Contact(
                    name=person.get("name", "").strip() or "Unknown",
                    title=person.get("title", "").strip(),
                    email=person.get("email") or "",
                    linkedin_url=person.get("linkedin_url") or "",
                )
            )
        if len(contacts) >= 4:
            break

    return contacts[:4]
