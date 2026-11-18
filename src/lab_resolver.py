import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROSTER_FILE = Path("data/iai_roster.json")
PAPERS_FILE = Path("data/papers_raw.json")

LAB_PATTERNS = (
    re.compile(r"\b(?:lab|laboratory|center|institute|group|clinic|collaborative)\b", re.I),
)


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def extract_labs(person: dict) -> list[str]:
    """Extract lab/center/group names from an IAI roster entry or profile."""
    title = person.get("title", "")
    text = " ".join(filter(None, (title, person.get("name", ""))))
    labs: list[str] = []

    for match in re.finditer(r"(?:director|head|coordinator|member|affiliate),\s*([^,;]+)", text, re.I):
        candidate = match.group(1).strip(" .")
        if LAB_PATTERNS[0].search(candidate):
            labs.append(candidate)

    lab_pattern = r"[A-Za-z0-9&/-]+(?: [A-Za-z0-9&/-]+){0,5} (?:Lab|Laboratory|Center|Institute|Group|Clinic)\b"
    for phrase in re.findall(lab_pattern, title, re.I):
        labs.append(phrase.strip())

    profile_url = person.get("profile_url")
    if profile_url:
        try:
            response = requests.get(profile_url, timeout=15)
            if response.ok:
                soup = BeautifulSoup(response.text, "html.parser")
                page_text = " ".join(soup.stripped_strings)
                for phrase in re.findall(lab_pattern, page_text, re.I):
                    labs.append(phrase.strip())
        except requests.RequestException:
            pass

    unique = []
    seen = set()
    for lab in labs:
        key = normalize_name(lab)
        if key and key not in seen:
            seen.add(key)
            unique.append(lab)
    return sorted(unique)


def resolve_labs() -> None:
    if not ROSTER_FILE.exists():
        raise FileNotFoundError(ROSTER_FILE)
    roster = json.loads(ROSTER_FILE.read_text())

    roster_by_name = {}
    for person in roster:
        labs = extract_labs(person)
        person["labs"] = labs
        key = person.get("normalized_name") or normalize_name(person.get("name", ""))
        if key:
            roster_by_name[key] = labs

    ROSTER_FILE.write_text(json.dumps(roster, indent=2) + "\n")

    if PAPERS_FILE.exists():
        papers = json.loads(PAPERS_FILE.read_text())
        for paper in papers:
            paper_labs: list[str] = []
            for author in paper.get("authors", []):
                labs = roster_by_name.get(normalize_name(author.get("name", "")), [])
                paper_labs.extend(labs)
            paper["uga_labs"] = sorted(set(paper_labs))
            paper["uga_lab"] = ", ".join(paper["uga_labs"])
        PAPERS_FILE.write_text(json.dumps(papers, indent=2) + "\n")

    print(f"Resolved labs for {len(roster)} roster members and updated papers.")


if __name__ == "__main__":
    resolve_labs()
