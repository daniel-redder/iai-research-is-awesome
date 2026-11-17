import json
import requests
import os
from datetime import datetime, timedelta
import re

BASE_URL = "https://api.openalex.org/works"
STATE_FILE = "data/harvest_state.json"
DATA_FILE = "data/papers_raw.json"
POLITE_EMAIL = os.environ.get("POLITE_EMAIL", "default@example.com")

def check_api_status():
    """Check if the API is available and we aren't rate-limited (429)."""
    res = requests.get(BASE_URL, params={"mailto": POLITE_EMAIL, "per-page": 1})
    if res.status_code == 429:
        print("Rate limit exceeded. Aborting today's run.")
        return False
    res.raise_for_status()
    return True

def fetch_batch(cursor_date, direction, limit=500):
    """Fetch papers either moving forward (asc) or backward (desc) in time."""
    papers = []
    page = 1
    new_cursor = cursor_date
    
    # Set date filter based on direction
    if direction == "forward":
        date_filter = f"from_publication_date:{cursor_date}"
        sort_order = "publication_date:asc"
    else:
        # Subtract a day for backward to avoid re-fetching the exact cursor date infinitely
        shifted_date = (datetime.strptime(cursor_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        date_filter = f"to_publication_date:{shifted_date}"
        sort_order = "publication_date:desc"

    while len(papers) < limit:
        params = {
            "filter": f"institutions.id:I167010486,concepts.id:C41008148,{date_filter}",
            "sort": sort_order,
            "per-page": min(200, limit - len(papers)),
            "page": page,
            "mailto": POLITE_EMAIL
        }
        
        response = requests.get(BASE_URL, params=params).json()
        results = response.get('results', [])
        
        if not results:
            break # No more papers in this direction
            
        for work in results:
            location = work.get('primary_location', {})
            venue = location.get('source', {}).get('display_name', 'Unknown') if location and location.get('source') else 'Unknown'
            
            papers.append({
                "id": work.get('id'),
                "title": work.get('title'),
                "venue": venue,
                "publication_date": work.get('publication_date'),
                "referenced_works": work.get('referenced_works', []),
                "authors": [{"id": a.get('author', {}).get('id'), "name": a.get('author', {}).get('display_name')} for a in work.get('authorships', [])],
                "abstract": work.get('abstract_inverted_index', {})
            })
            new_cursor = work.get('publication_date') or new_cursor
            
        page += 1

    return papers, new_cursor

def run_daily_harvest():
    if not check_api_status():
        return

    # Load or initialize state
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    else:
        state = {"forward_cursor": today_str, "backward_cursor": today_str}

    print(f"Starting harvest. Forward cursor: {state['forward_cursor']}, Backward cursor: {state['backward_cursor']}")

    # Load existing papers
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            existing_papers = json.load(f)
    else:
        existing_papers = []
        
    existing_ids = {p['id'] for p in existing_papers}

    # Fetch 500 forward and 500 backward
    forward_papers, new_fwd_cursor = fetch_batch(state["forward_cursor"], "forward", limit=500)
    backward_papers, new_bwd_cursor = fetch_batch(state["backward_cursor"], "backward", limit=500)

    # Deduplicate and append
    new_papers = 0
    for p in forward_papers + backward_papers:
        if p['id'] not in existing_ids:
            existing_papers.append(p)
            existing_ids.add(p['id'])
            new_papers += 1

    # Save updated data
    with open(DATA_FILE, "w") as f:
        json.dump(existing_papers, f, indent=2)

    # Update and save state
    state["forward_cursor"] = new_fwd_cursor
    state["backward_cursor"] = new_bwd_cursor
    state["last_run"] = today_str
    
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    update_readme_badges(state["backward_cursor"], state["forward_cursor"])

    print(f"Harvest complete. Added {new_papers} new papers. Total: {len(existing_papers)}.")
    print(f"New cursors -> Forward: {new_fwd_cursor}, Backward: {new_bwd_cursor}")




def update_readme_badges(backward_cursor, forward_cursor):
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        return
        
    with open(readme_path, "r") as f:
        content = f.read()

    today_str = datetime.now(tz=datetime.timezone.utc).strftime("%Y--%m--%d")
    safe_backward = backward_cursor.replace("-", "--")
    safe_forward = forward_cursor.replace("-", "--")
    
    # Regex replace the badges
    content = re.sub(
        r'Last_Updated-.*?-blue', 
        f'Last_Updated-{today_str}-blue', 
        content
    )
    content = re.sub(
        r'Breadth-.*?-green', 
        f'Breadth-{safe_backward}_to_{safe_forward}-green', 
        content
    )

    with open(readme_path, "w") as f:
        f.write(content)


if __name__ == "__main__":
    run_daily_harvest()