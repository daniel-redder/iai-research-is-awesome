import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROSTER_FILE = Path("data/iai_roster.json")
PAPERS_FILE = Path("data/papers_raw.json")
UNCERTAIN_LAB = "Uncertain"

LAB_NAME_PATTERN = re.compile(
    r"\b((?:[A-Z][A-Za-z0-9&/-]*|and|of|for|the|in|on|at)"
    r"(?:\s+(?:[A-Z][A-Za-z0-9&/-]*|and|of|for|the|in|on|at)){0,7}"
    r"\s+(?:[Ll]ab|[Ll]aboratory|[Cc]enter|[Ii]nstitute|[Gg]roup|[Cc]linic))\b"
)
LAB_SUFFIX_PATTERN = re.compile(r"\b(lab|laboratory|center|institute|group|clinic)\b", re.I)
LAB_NOISE_PATTERN = re.compile(
    r"\b(?:events|resources|contact|directory|fellows|industry|office|room|suite|"
    r"street|avenue|building|campus|description|vision|seminar)\b|\b\d{2,}\b",
    re.I,
)
LAB_CONTEXT_PATTERN = re.compile(
    r"\b(?:director|professor|lecturer|fellow|postdoctoral|faculty|department|school|college)\b",
    re.I,
)
GENERIC_LAB_NAMES = {
    "and lab",
    "and group",
    "group",
    "lab",
    "a lab",
    "his lab",
    "her lab",
    "my lab",
    "their lab",
    "the lab",
    "the laboratory",
    "the center",
    "the institute",
    "the group",
    "the clinic",
    "the director of the institute",
}
UGA_LAB_ALIASES = {
    "AI4STEM Education Center": "AI4STEM Education Center",
    "Cox International Center": "Cox International Center",
    "Developmental Dynamics Lab": "Developmental Dynamics Lab",
    "Design Informatics and Computational Engineering Lab": "Design Informatics and Computational Engineering Lab",
    "Douglass Lab": "Douglass Lab",
    "Engineering Education Transformations Institute": "Engineering Education Transformations Institute",
    "Global Health Institute": "Global Health Institute",
    "HeRo Lab": "HeRo Lab",
    "Kay Ivester Institute": "Kay Ivester Institute",
    "Liu Group": "Liu Group",
    "MODEL Research Group": "MODEL Research Group",
    "Neurocognition Science Laboratory": "Neurocognition Science Laboratory",
    "Optical Sensing Laboratory": "Optical Sensing Laboratory",
    "Pete Bettinger Research Group": "Pete Bettinger Research Group",
    "Ping Ma Lab": "The Ma Lab",
    "Precision Management/Well Being Lab": "Precision Management/Well Being Lab",
    "RAIL Lab": "RAIL Lab",
    "The RAIL Lab": "RAIL Lab",
    "River Basin Center": "River Basin Center",
    "Second Language Acquisition and Cognition Lab": "Second Language Acquisition and Cognition Lab",
    "Skidaway Institute": "Skidaway Institute",
    "SMART Lab": "SMART Lab",
    "Song Lab": "Song Lab",
    "The Computational Agriculture Lab": "The Computational Agriculture Lab",
    "The Computational Multi-Modal Communication Lab": "The Computational Multi-Modal Communication Lab",
    "The Creativity and Imagination Lab": "The Creativity and Imagination Lab",
    "The Data-Intensive Pervasive Systems Lab": "The Data-Intensive Pervasive Systems Lab",
    "The Evolutionary Computation and Machine Learning Laboratory": "The Evolutionary Computation and Machine Learning Laboratory",
    "The Heterogeneous Robotics Research Lab": "The Heterogeneous Robotics Research Lab",
    "The Hoarfrost Lab": "The Hoarfrost Lab",
    "The Human Factors and Aging Laboratory": "The Human Factors and Aging Laboratory",
    "The Ma Lab": "The Ma Lab",
    "The Mobility Lab": "The Mobility Lab",
    "The Owens Institute": "The Owens Institute",
    "The Physical AI in Smart Manufacturing Lab": "The Physical AI in Smart Manufacturing Lab",
    "The Rett Lab": "The Rett Lab",
    "The River Basin Center": "River Basin Center",
    "The Small Satellite Research Laboratory": "The Small Satellite Research Laboratory",
    "The Sundaram Lab": "The Sundaram Lab",
    "THINC Lab": "THINC Lab",
    "The Virtual Experiences Laboratory": "The Virtual Experiences Laboratory",
    "The Zhang Lab": "The Zhang Lab",
    "Torrance Center": "Torrance Center",
    "UGA Bioimaging Research Center": "UGA Bioimaging Research Center",
    "UGA Small Satellite Research Laboratory": "The Small Satellite Research Laboratory",
    "University of Georgia Cancer Center": "University of Georgia Cancer Center",
    "Virtual Experiences Laboratory": "The Virtual Experiences Laboratory",
    "Zhao Research Group": "Zhao Research Group",
}


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


UGA_LAB_NAME_MAP = {
    normalize_name(alias): canonical for alias, canonical in UGA_LAB_ALIASES.items()
}


def uga_lab_name(value: str) -> str | None:
    """Return the canonical name only for labs and centers recognized as UGA units."""
    return UGA_LAB_NAME_MAP.get(normalize_name(value))


def clean_lab_name(value: str) -> str:
    """Keep a concise lab-like name, or mark the source as uncertain."""
    if not value or LAB_NOISE_PATTERN.search(value):
        return UNCERTAIN_LAB

    candidates = LAB_NAME_PATTERN.findall(value)
    if not candidates:
        return UNCERTAIN_LAB

    candidate = candidates[-1].strip(" .,:;-()")
    candidate = re.sub(r"^(?:(?:and|of|for|in|on|at)\s+)+", "", candidate, flags=re.I)
    if normalize_name(candidate) in GENERIC_LAB_NAMES or LAB_CONTEXT_PATTERN.search(candidate):
        return UNCERTAIN_LAB

    suffix_matches = list(LAB_SUFFIX_PATTERN.finditer(candidate))
    if not suffix_matches:
        return UNCERTAIN_LAB
    suffix_match = suffix_matches[-1]
    suffix = suffix_match.group(1).capitalize()
    candidate = candidate[: suffix_match.start(1)] + suffix
    return re.sub(r"^the\b", "The", candidate)


def extract_labs(person: dict) -> list[str]:
    """Extract lab/center/group names from an IAI roster entry or profile."""
    title = person.get("title", "")
    text = " ".join(filter(None, (title, person.get("name", ""))))
    labs: list[str] = []

    for match in re.finditer(
        r"(?:director|head|coordinator|member|affiliate),\s*([^,;]+)", text, re.I
    ):
        candidate = match.group(1).strip(" .")
        if LAB_SUFFIX_PATTERN.search(candidate):
            labs.append(candidate)

    for phrase in LAB_NAME_PATTERN.findall(title):
        labs.append(phrase.strip())

    profile_url = person.get("profile_url")
    if profile_url:
        try:
            response = requests.get(profile_url, timeout=15)
            if response.ok:
                soup = BeautifulSoup(response.text, "html.parser")
                page_text = " ".join(soup.stripped_strings)
                for phrase in LAB_NAME_PATTERN.findall(page_text):
                    labs.append(phrase.strip())
        except requests.RequestException:
            pass

    unique = []
    seen = set()
    for lab in labs:
        lab = uga_lab_name(clean_lab_name(lab))
        if not lab:
            continue
        key = normalize_name(lab)
        if key and key not in seen:
            seen.add(key)
            unique.append(lab)
    return sorted(unique) if unique else [UNCERTAIN_LAB]


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
                paper_labs.extend(lab for lab in labs if lab != UNCERTAIN_LAB)
            paper["uga_labs"] = sorted(set(paper_labs))
            paper["uga_lab"] = ", ".join(paper["uga_labs"])
        PAPERS_FILE.write_text(json.dumps(papers, indent=2) + "\n")

    print(f"Resolved labs for {len(roster)} roster members and updated papers.")


if __name__ == "__main__":
    resolve_labs()
