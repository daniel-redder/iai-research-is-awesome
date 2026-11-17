import json
import requests
import os
from datetime import datetime, timedelta
import re
import time
import random
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.openalex.org/works"
STATE_FILE = "data/harvest_state.json"
DATA_FILE = "data/papers_raw.json"
POLITE_EMAIL = os.environ.get("POLITE_EMAIL", "default@example.com")
OPENALEX_API_KEY = os.environ.get("OPENALEX_API_KEY")
MAX_REQUESTS_PER_RUN = int(os.environ.get("OPENALEX_MAX_REQUESTS", "8"))
MAX_RETRIES = int(os.environ.get("OPENALEX_MAX_RETRIES", "5"))
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("OPENALEX_TIMEOUT_SECONDS", "30"))

def check_api_status(request_counter=None):
    """Check API availability without retrying forever or exceeding budget."""
    counter = request_counter or {"count": 0}
    try:
        openalex_get({"per-page": 1}, counter)
        return True
    except RuntimeError as error:
        print(error)
        return False

def fetch_batch(cursor_date, direction, limit=500, request_counter=None):
    """Fetch papers either moving forward (asc) or backward (desc) in time."""
    papers = []
    page = 1
    new_cursor = cursor_date
    counter = request_counter or {"count": 0}
    
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
        response = openalex_get({
            "filter": f"institutions.id:I167010486,concepts.id:C41008148,{date_filter}",
            "sort": sort_order,
            "per-page": min(200, limit - len(papers)),
            "page": page,
            "select": "id,title,publication_date,primary_location,authorships,referenced_works,abstract_inverted_index,doi"
        }, counter)
        
        results = response.get('results', [])
        
        if not results:
            break # No more papers in this direction
            
        for work in results:
            location = work.get('primary_location', {})
            venue = location.get('source', {}).get('display_name', 'Unknown') if location and location.get('source') else 'Unknown'
            landing_page = location.get('landing_page_url') or work.get('doi')
            url = landing_page or (f"https://openalex.org/{work.get('id', '').rsplit('/', 1)[-1]}" if work.get('id') else None)
            
            papers.append({
                "id": work.get('id'),
                "title": work.get('title'),
                "url": url,
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
    request_counter = {"count": 0}
    if not check_api_status(request_counter):
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
    try:
        forward_papers, new_fwd_cursor = fetch_batch(state["forward_cursor"], "forward", limit=200, request_counter=request_counter)
        backward_papers, new_bwd_cursor = fetch_batch(state["backward_cursor"], "backward", limit=200, request_counter=request_counter)
    except RuntimeError as error:
        print(f"Harvest stopped safely: {error}. Requests used: {request_counter['count']}/{MAX_REQUESTS_PER_RUN}")
        return

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


def openalex_request_options(extra_params=None):
    """Build query parameters and headers for optional OpenAlex authentication."""
    params = dict(extra_params or {})
    params["mailto"] = POLITE_EMAIL
    headers = {}
    if OPENALEX_API_KEY:
        params["api_key"] = OPENALEX_API_KEY
        headers["Authorization"] = f"Bearer {OPENALEX_API_KEY}"
    return params, headers


def openalex_get(params, request_counter, retry_count=0):
    """GET OpenAlex with exponential backoff for 429/5xx responses."""
    if request_counter["count"] >= MAX_REQUESTS_PER_RUN:
        raise RuntimeError("OpenAlex request budget exhausted")

    params, headers = openalex_request_options(params)
    request_counter["count"] += 1

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.RequestException as error:
        if retry_count >= MAX_RETRIES:
            raise RuntimeError("OpenAlex request failed after retries") from error
        delay = min(60, (2 ** retry_count) + random.uniform(0, 1))
        print(f"OpenAlex network error; retrying in {delay:.1f}s")
        time.sleep(delay)
        return openalex_get(params, request_counter, retry_count + 1)

    if response.status_code == 429:
        if retry_count >= MAX_RETRIES:
            raise RuntimeError("OpenAlex rate limit persists; run aborted")
        retry_after = response.headers.get("Retry-After")
        delay = float(retry_after) if retry_after and retry_after.isdigit() else min(60, (2 ** retry_count) + random.uniform(0, 1))
        print(f"OpenAlex 429; retrying in {delay:.1f}s")
        time.sleep(delay)
        return openalex_get(params, request_counter, retry_count + 1)

    if 500 <= response.status_code < 600:
        if retry_count >= MAX_RETRIES:
            raise RuntimeError("OpenAlex server error persists; run aborted")
        delay = min(60, (2 ** retry_count) + random.uniform(0, 1))
        print(f"OpenAlex {response.status_code}; retrying in {delay:.1f}s")
        time.sleep(delay)
        return openalex_get(params, request_counter, retry_count + 1)

    if response.status_code in (401, 403, 402):
        raise RuntimeError("OpenAlex authentication or API budget denied; run aborted")

    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    run_daily_harvest()