import json
import os

def resolve_authors():
    if not os.path.exists("data/papers_raw.json"):
        return
        
    with open("data/papers_raw.json", "r") as f:
        papers = json.load(f)
        
    # Load existing master author list if it exists
    authors_db_path = "data/authors_master.json"
    if os.path.exists(authors_db_path):
        with open(authors_db_path, "r") as f:
            authors_db = json.load(f)
    else:
        authors_db = {}
        
    # Mock list of known IAI faculty (In practice, pull from a GSheet or CSV)
    known_core = ["Jae Wook Lee", "Tianming Liu", "Kyle Johnsen"]
    known_affiliate = ["Sun Joo Ahn"]
        
    for paper in papers:
        for author in paper.get("authors", []):
            auth_id = author["id"]
            auth_name = author["name"]
            
            if auth_id not in authors_db:
                # Determine status
                status = "Uncertain"
                if auth_name in known_core:
                    status = "IAI Core"
                elif auth_name in known_affiliate:
                    status = "IAI Affiliate"
                    
                authors_db[auth_id] = {
                    "name": auth_name,
                    "status": status,
                    "paper_count": 0
                }
            
            authors_db[auth_id]["paper_count"] += 1
            
    with open(authors_db_path, "w") as f:
        json.dump(authors_db, f, indent=2)
        
    print(f"Resolved {len(authors_db)} unique authors.")

if __name__ == "__main__":
    resolve_authors()
