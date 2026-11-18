import json
import os
import re


def normalize_name(name):
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def resolve_authors():
    if not os.path.exists("data/papers_raw.json"):
        return

    with open("data/papers_raw.json", "r") as f:
        papers = json.load(f)

    authors_db_path = "data/authors_master.json"
    if os.path.exists(authors_db_path):
        with open(authors_db_path, "r") as f:
            authors_db = json.load(f)
    else:
        authors_db = {}

    roster_path = "data/iai_roster.json"
    if os.path.exists(roster_path):
        with open(roster_path, "r") as f:
            roster = json.load(f)
    else:
        roster = []

    roster_by_name = {
        person["normalized_name"]: person for person in roster if person.get("normalized_name")
    }

    for paper in papers:
        uga_author_ids = []
        for author in paper.get("authors", []):
            auth_id = author["id"]
            auth_name = author["name"]
            normalized_name = normalize_name(auth_name)
            roster_person = roster_by_name.get(normalized_name)

            status = roster_person["status"] if roster_person else "Uncertain"

            if auth_id not in authors_db:
                authors_db[auth_id] = {
                    "name": auth_name,
                    "status": status,
                    "paper_count": 0,
                }
            else:
                authors_db[auth_id]["name"] = auth_name
                authors_db[auth_id]["status"] = status

            authors_db[auth_id]["paper_count"] += 1
            if roster_person and auth_id:
                uga_author_ids.append(auth_id)

        paper["uga_authors"] = sorted(set(filter(None, uga_author_ids)), key=str)

    with open(authors_db_path, "w") as f:
        json.dump(authors_db, f, indent=2)

    with open("data/papers_raw.json", "w") as f:
        json.dump(papers, f, indent=2)

    print(f"Resolved {len(authors_db)} unique authors.")


if __name__ == "__main__":
    resolve_authors()
