import json
import re
import time
from pathlib import Path
import datetime

import requests
from bs4 import BeautifulSoup

DIRECTORY_URL = "https://www.ai.uga.edu/directory/all"
ROSTER_FILE = Path("data/iai_roster.json")
WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"


def classify(title: str) -> str:
    lowered = title.lower()
    if re.search(r"\bcore\b", lowered):
        return "Core"
    if re.search(r"\baffiliate\b", lowered):
        return "Affiliate"
    if re.search(r"\bfellow\b", lowered):
        return "Fellow"
    if re.search(r"student|doctoral|phd", lowered):
        return "Student"
    if "institute for ai" in lowered or "institute for artificial intelligence" in lowered:
        return "Core"
    return "Uncertain"


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def refresh_roster() -> list[dict]:
    response = requests.get(DIRECTORY_URL, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    roster = []
    seen = set()

    for card in soup.select("div.views-row"):
        name_heading = card.select_one("h2")
        profile_link = card.select_one("a[href*='/directory/people/']")
        job = card.select_one(".views-field-field-job-title")
        email_link = card.select_one("a[href^='mailto:']")

        if not name_heading:
            continue

        name = " ".join(name_heading.stripped_strings)
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())

        title = " ".join(job.stripped_strings) if job else ""
        email = ""
        if email_link:
            email = email_link.get("href", "").removeprefix("mailto:").strip()

        profile_url = ""
        if profile_link:
            profile_url = profile_link.get("href", "")
            if profile_url.startswith("/"):
                profile_url = "https://www.ai.uga.edu" + profile_url

        roster.append(
            {
                "name": name,
                "normalized_name": normalize_name(name),
                "status": classify(title),
                "title": title,
                "email": email,
                "profile_url": profile_url,
                "source": DIRECTORY_URL,
            }
        )

    roster.sort(key=lambda person: person["name"])
    ROSTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    ROSTER_FILE.write_text(json.dumps(roster, indent=2) + "\n")
    print(f"Wrote {len(roster)} people to {ROSTER_FILE}")
    return roster


def fetch_historical_roster(year: int) -> list[dict]:
    params = (
        ("url", "www.ai.uga.edu/directory/all"),
        ("from", str(year)),
        ("to", str(year)),
        ("output", "json"),
        ("filter", "statuscode:200"),
        ("filter", "mimetype:text/html"),
        ("collapse", "digest"),
        ("fl", "timestamp,original"),
    )
    response = None
    for attempt in range(4):
        try:
            response = requests.get(
                WAYBACK_CDX,
                params=params,
                timeout=30,
                headers={"User-Agent": "UGA-IAI-Research-Pipeline/1.0"},
            )
            if response.status_code == 429:
                time.sleep(2**attempt)
                continue
            response.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 3:
                return []
            time.sleep(2**attempt)

    if response is None:
        return []

    rows = response.json()
    if len(rows) < 2:
        return []

    snapshot = rows[-1][0]
    archived_url = f"https://web.archive.org/web/{snapshot}/https://www.ai.uga.edu/directory/all"
    archived = requests.get(archived_url, timeout=30)
    archived.raise_for_status()
    soup = BeautifulSoup(archived.text, "html.parser")

    people = []
    for card in soup.select("div.views-row"):
        name_heading = card.select_one("h2")
        legacy_name = card.select_one(".wrap2_personnel")
        if name_heading:
            name = " ".join(name_heading.stripped_strings)
        elif legacy_name:
            name = " ".join(legacy_name.stripped_strings)
            if "," in name:
                last, first = (part.strip() for part in name.split(",", 1))
                name = f"{first} {last}".strip()
        else:
            continue

        job = card.select_one(".views-field-field-job-title")
        title = " ".join(job.stripped_strings) if job else ""
        email_link = card.select_one("a[href^='mailto:']")
        email = email_link.get("href", "").removeprefix("mailto:").strip() if email_link else ""

        people.append(
            {
                "name": name,
                "normalized_name": normalize_name(name),
                "status": classify(title),
                "title": title,
                "email": email,
                "profile_url": "",
                "source": archived_url,
                "first_seen_year": year,
                "last_seen_year": year,
            }
        )
    return people


if __name__ == "__main__":
    roster = refresh_roster()

    roster_by_name = {person["normalized_name"]: person for person in roster}

    for year in range(2018, 2027):
        try:
            historical = fetch_historical_roster(year)
            for person in historical:
                key = person["normalized_name"]
                if not key:
                    continue
                if key in roster_by_name:
                    roster_by_name[key]["first_seen_year"] = min(
                        roster_by_name[key].get("first_seen_year", year), year
                    )
                    roster_by_name[key]["last_seen_year"] = max(
                        roster_by_name[key].get("last_seen_year", year), year
                    )
                else:
                    roster_by_name[key] = person
                    roster.append(person)
            time.sleep(1)
        except requests.RequestException:
            continue

    current_year = datetime.datetime.now().year
    for person in roster:
        person["first_seen_year"] = person.get("first_seen_year", current_year)
        person["last_seen_year"] = person.get("last_seen_year", current_year)

    roster.sort(key=lambda person: person["name"])
    ROSTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    ROSTER_FILE.write_text(json.dumps(roster, indent=2) + "\n")
    print(f"Wrote {len(roster)} people to {ROSTER_FILE}")
