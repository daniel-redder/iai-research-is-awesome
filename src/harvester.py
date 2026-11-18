import json
import requests
import os
import argparse
import calendar
from datetime import datetime, timedelta, timezone
import re
import time
import random
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.openalex.org/works"
STATE_FILE = "data/harvest_state.json"
DATA_FILE = "data/papers_raw.json"
POLITE_EMAIL = os.environ.get("POLITE_EMAIL", "default@example.com")
OPENALEX_API_KEY = os.environ.get("OPENALEX_API_KEY")
OPENALEX_INSTITUTION_ID = os.environ.get("OPENALEX_INSTITUTION_ID", "I165733156")
OPENALEX_CONCEPT_ID = os.environ.get("OPENALEX_CONCEPT_ID", "C41008148")
MAX_REQUESTS_PER_RUN = int(os.environ.get("OPENALEX_MAX_REQUESTS", "8"))
MAX_FAILED_REQUESTS_PER_RUN = int(os.environ.get("OPENALEX_MAX_FAILED_REQUESTS", "25"))
MAX_RETRIES = int(os.environ.get("OPENALEX_MAX_RETRIES", "5"))
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("OPENALEX_TIMEOUT_SECONDS", "30"))

ROSTER_FILE = "data/iai_roster.json"
MAX_TEXT_FIELD_LEN = 2000
MAX_AUTHORS_PER_PAPER = 200
MAX_REFERENCES_PER_PAPER = 2000
MAX_ABSTRACT_TERMS = 10000
MAX_ABSTRACT_POSITION = 50000


def safe_text(value, max_len=MAX_TEXT_FIELD_LEN):
    text = value if isinstance(value, str) else ""
    # Strip control characters while preserving whitespace needed for readability.
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    text = text.strip()
    return text[:max_len]


def safe_identifier(value, max_len=256):
    text = safe_text(value, max_len=max_len)
    return text or None


def safe_date(value):
    text = safe_text(value, max_len=32)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    return None


def safe_url(value):
    text = safe_text(value, max_len=2048)
    if not text:
        return None
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return text
    return None


def sanitize_referenced_works(works):
    if not isinstance(works, list):
        return []
    cleaned = []
    seen = set()
    for work_id in works[:MAX_REFERENCES_PER_PAPER]:
        normalized = safe_identifier(work_id)
        if normalized and normalized not in seen:
            seen.add(normalized)
            cleaned.append(normalized)
    return cleaned


def sanitize_authorships(authorships):
    if not isinstance(authorships, list):
        return []
    authors = []
    for authorship in authorships[:MAX_AUTHORS_PER_PAPER]:
        if not isinstance(authorship, dict):
            continue
        author = authorship.get("author", {})
        if not isinstance(author, dict):
            continue
        author_id = safe_identifier(author.get("id"))
        author_name = safe_text(author.get("display_name"), max_len=200)
        authors.append({"id": author_id, "name": author_name or "Unknown author"})
    return authors


def sanitize_abstract_index(index):
    if not isinstance(index, dict):
        return {}

    cleaned = {}
    remaining_terms = MAX_ABSTRACT_TERMS

    for token, positions in index.items():
        if remaining_terms <= 0:
            break
        safe_token = safe_text(token, max_len=80)
        if not safe_token or not isinstance(positions, list):
            continue

        safe_positions = []
        for position in positions:
            if not isinstance(position, int):
                continue
            if 0 <= position <= MAX_ABSTRACT_POSITION:
                safe_positions.append(position)
                remaining_terms -= 1
                if remaining_terms <= 0:
                    break

        if safe_positions:
            cleaned[safe_token] = safe_positions

    return cleaned


def normalize_name(name):
    return re.sub(r"[^a-z0-9]+", " ", safe_text(name, max_len=200).lower()).strip()


def load_roster_names():
    if not os.path.exists(ROSTER_FILE):
        return set()
    with open(ROSTER_FILE, "r") as f:
        roster = json.load(f)
    if not isinstance(roster, list):
        return set()
    return {
        person.get("normalized_name") or normalize_name(person.get("name"))
        for person in roster
        if isinstance(person, dict) and (person.get("normalized_name") or person.get("name"))
    }


ROSTER_AUTHOR_NAMES = load_roster_names()


def check_api_status(request_counter=None, failed_request_counter=None):
    """Check API availability without retrying forever or exceeding budget."""
    counter = request_counter or {"count": 0}
    failed_counter = failed_request_counter or {"count": 0}
    try:
        openalex_get({"per-page": 1}, counter, failed_counter)
        return True
    except RuntimeError as error:
        print(error)
        return False


def fetch_batch(
    cursor_date,
    direction,
    limit=500,
    lower_bound_date=None,
    upper_bound_date=None,
    request_counter=None,
    failed_request_counter=None,
):
    """Fetch papers either moving forward (asc) or backward (desc) in time."""
    papers = []
    page = 1
    new_cursor = cursor_date
    counter = request_counter or {"count": 0}
    failed_counter = failed_request_counter or {"count": 0}

    # Set date filter based on direction
    if direction == "forward":
        date_filters = [f"from_publication_date:{cursor_date}"]
        if upper_bound_date:
            date_filters.append(f"to_publication_date:{upper_bound_date}")
        sort_order = "publication_date:asc"
    else:
        # Subtract a day for backward to avoid re-fetching the exact cursor date infinitely
        shifted_date = (datetime.strptime(cursor_date, "%Y-%m-%d") - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )
        date_filters = [f"to_publication_date:{shifted_date}"]
        if lower_bound_date:
            date_filters.append(f"from_publication_date:{lower_bound_date}")
        sort_order = "publication_date:desc"

    while len(papers) < limit:
        response = openalex_get(
            {
                "filter": ",".join(
                    [
                        f"institutions.id:{OPENALEX_INSTITUTION_ID}",
                        f"concepts.id:{OPENALEX_CONCEPT_ID}",
                        *date_filters,
                    ]
                ),
                "sort": sort_order,
                "per-page": min(200, limit - len(papers)),
                "page": page,
                "select": "id,title,publication_date,primary_location,authorships,referenced_works,abstract_inverted_index,doi",
            },
            counter,
            failed_counter,
        )

        results = response.get("results", [])

        if not results:
            break  # No more papers in this direction

        for work in results:
            if not isinstance(work, dict):
                continue

            location = work.get("primary_location", {})
            if not isinstance(location, dict):
                location = {}
            venue = (
                location.get("source", {}).get("display_name", "Unknown")
                if location and location.get("source")
                else "Unknown"
            )
            venue = safe_text(venue, max_len=400) or "Unknown"
            landing_page = location.get("landing_page_url") or work.get("doi")
            url = safe_url(landing_page) or (
                f"https://openalex.org/{work.get('id', '').rsplit('/', 1)[-1]}"
                if work.get("id")
                else None
            )
            url = safe_url(url)

            authorships = work.get("authorships", [])
            if not isinstance(authorships, list):
                authorships = []

            # Filter out works without any authors on the IAI roster
            if not any(
                normalize_name(a.get("author", {}).get("display_name")) in ROSTER_AUTHOR_NAMES
                for a in authorships
                if isinstance(a, dict)
            ):
                continue

            safe_work_id = safe_identifier(work.get("id"))
            if not safe_work_id:
                continue

            papers.append(
                {
                    "id": safe_work_id,
                    "title": safe_text(work.get("title"), max_len=2000) or "Untitled",
                    "url": url,
                    "venue": venue,
                    "publication_date": safe_date(work.get("publication_date")),
                    "referenced_works": sanitize_referenced_works(work.get("referenced_works", [])),
                    "authors": sanitize_authorships(authorships),
                    "abstract": sanitize_abstract_index(work.get("abstract_inverted_index", {})),
                }
            )
            new_cursor = safe_date(work.get("publication_date")) or new_cursor

        page += 1

    return papers, new_cursor


def shift_datetime_by_unit(base_datetime, value, unit):
    """Shift a datetime by signed relative units."""
    normalized_unit = (unit or "").strip().lower()
    if normalized_unit.endswith("s"):
        normalized_unit = normalized_unit[:-1]

    if normalized_unit == "day":
        return base_datetime + timedelta(days=value)
    if normalized_unit == "week":
        return base_datetime + timedelta(weeks=value)
    if normalized_unit == "year":
        return shift_datetime_by_unit(base_datetime, value * 12, "month")
    if normalized_unit != "month":
        raise ValueError("Unsupported unit. Use days, weeks, months, or years.")

    month_index = (base_datetime.month - 1) + value
    target_year = base_datetime.year + (month_index // 12)
    target_month = (month_index % 12) + 1
    target_day = min(base_datetime.day, calendar.monthrange(target_year, target_month)[1])

    return base_datetime.replace(year=target_year, month=target_month, day=target_day)


def resolve_relative_timeframe(start_relative=None, end_relative=None, now=None):
    """Resolve relative CLI offsets to YYYY-MM-DD bounds.

    -s/--start interprets offset as now + offset.
    -e/--end interprets offset as now - offset.
    """
    reference_now = now or datetime.now(timezone.utc)

    start_date = None
    if start_relative:
        start_amount = int(start_relative[0])
        start_unit = start_relative[1]
        start_date = shift_datetime_by_unit(reference_now, start_amount, start_unit).strftime(
            "%Y-%m-%d"
        )

    end_date = None
    if end_relative:
        end_amount = int(end_relative[0])
        end_unit = end_relative[1]
        end_date = shift_datetime_by_unit(reference_now, -end_amount, end_unit).strftime("%Y-%m-%d")

    if start_date and end_date and start_date > end_date:
        raise ValueError(f"Resolved start date {start_date} is after end date {end_date}.")

    return start_date, end_date


def run_daily_harvest(start_date=None, end_date=None):
    request_counter = {"count": 0}
    failed_request_counter = {"count": 0}
    if not check_api_status(request_counter, failed_request_counter):
        return

    # Load or initialize state
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    else:
        state = {"forward_cursor": today_str, "backward_cursor": today_str}

    forward_cursor = start_date or state["forward_cursor"]
    backward_cursor = end_date or state["backward_cursor"]

    print(f"Starting harvest. Forward cursor: {forward_cursor}, Backward cursor: {backward_cursor}")

    # Load existing papers
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            existing_papers = json.load(f)
        if not isinstance(existing_papers, list):
            existing_papers = []
    else:
        existing_papers = []

    existing_ids = {p.get("id") for p in existing_papers if isinstance(p, dict) and p.get("id")}

    # Fetch 500 forward and 500 backward
    try:
        forward_papers, new_fwd_cursor = fetch_batch(
            forward_cursor,
            "forward",
            limit=200,
            upper_bound_date=end_date,
            request_counter=request_counter,
            failed_request_counter=failed_request_counter,
        )
        backward_papers, new_bwd_cursor = fetch_batch(
            backward_cursor,
            "backward",
            limit=200,
            lower_bound_date=start_date,
            request_counter=request_counter,
            failed_request_counter=failed_request_counter,
        )
    except RuntimeError as error:
        print(
            f"Harvest stopped safely: {error}. Requests used: {request_counter['count']}/{MAX_REQUESTS_PER_RUN}. "
            f"Failed requests: {failed_request_counter['count']}/{MAX_FAILED_REQUESTS_PER_RUN}"
        )
        return

    # Deduplicate and append
    new_papers = 0
    for p in forward_papers + backward_papers:
        paper_id = p.get("id") if isinstance(p, dict) else None
        if paper_id and paper_id not in existing_ids:
            existing_papers.append(p)
            existing_ids.add(paper_id)
            new_papers += 1

    # Save updated data
    with open(DATA_FILE, "w") as f:
        json.dump(existing_papers, f, indent=2)

    # Keep normal cursor progression unless running a bounded one-off range query.
    if start_date or end_date:
        print("Range mode enabled; state cursors were not updated.")
    else:
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

    today_str = datetime.now(tz=timezone.utc).strftime("%Y--%m--%d")
    safe_backward = backward_cursor.replace("-", "--")
    safe_forward = forward_cursor.replace("-", "--")

    # Regex replace the badges
    content = re.sub(r"Last_Updated-.*?-blue", f"Last_Updated-{today_str}-blue", content)
    content = re.sub(
        r"Breadth-.*?-green", f"Breadth-{safe_backward}_to_{safe_forward}-green", content
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


def openalex_get(params, request_counter, failed_request_counter=None, retry_count=0):
    """GET OpenAlex with exponential backoff for 429/5xx responses."""
    failed_counter = failed_request_counter or {"count": 0}

    if retry_count > 0 and failed_counter["count"] >= MAX_FAILED_REQUESTS_PER_RUN:
        raise RuntimeError("OpenAlex failed request budget exhausted")

    if request_counter["count"] >= MAX_REQUESTS_PER_RUN:
        raise RuntimeError("OpenAlex request budget exhausted")

    params, headers = openalex_request_options(params)
    request_counter["count"] += 1

    try:
        response = requests.get(
            BASE_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.RequestException as error:
        failed_counter["count"] += 1
        if retry_count >= MAX_RETRIES:
            raise RuntimeError("OpenAlex request failed after retries") from error
        delay = min(60, (2**retry_count) + random.uniform(0, 1))
        print(
            "DEBUG OpenAlexBackoff "
            f"status_code=NETWORK_ERROR retry_attempt={retry_count + 1}/{MAX_RETRIES} "
            f"backoff_seconds={delay:.1f} "
            f"failed_requests={failed_counter['count']}/{MAX_FAILED_REQUESTS_PER_RUN}"
        )
        time.sleep(delay)
        return openalex_get(params, request_counter, failed_counter, retry_count + 1)

    if response.status_code == 429:
        failed_counter["count"] += 1
        if retry_count >= MAX_RETRIES:
            raise RuntimeError("OpenAlex rate limit persists; run aborted")
        retry_after = response.headers.get("Retry-After")
        try:
            delay = float(retry_after) if retry_after else None
        except (TypeError, ValueError):
            delay = None
        if delay is None:
            delay = min(60, (2**retry_count) + random.uniform(0, 1))
        print(
            "DEBUG OpenAlexBackoff "
            f"status_code={response.status_code} retry_attempt={retry_count + 1}/{MAX_RETRIES} "
            f"backoff_seconds={delay:.1f} "
            f"failed_requests={failed_counter['count']}/{MAX_FAILED_REQUESTS_PER_RUN}"
        )
        time.sleep(delay)
        return openalex_get(params, request_counter, failed_counter, retry_count + 1)

    if 500 <= response.status_code < 600:
        failed_counter["count"] += 1
        if retry_count >= MAX_RETRIES:
            raise RuntimeError("OpenAlex server error persists; run aborted")
        delay = min(60, (2**retry_count) + random.uniform(0, 1))
        print(
            "DEBUG OpenAlexBackoff "
            f"status_code={response.status_code} retry_attempt={retry_count + 1}/{MAX_RETRIES} "
            f"backoff_seconds={delay:.1f} "
            f"failed_requests={failed_counter['count']}/{MAX_FAILED_REQUESTS_PER_RUN}"
        )
        time.sleep(delay)
        return openalex_get(params, request_counter, failed_counter, retry_count + 1)

    if response.status_code in (401, 403, 402):
        raise RuntimeError("OpenAlex authentication or API budget denied; run aborted")

    response.raise_for_status()
    return response.json()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Harvest OpenAlex papers for UGA AI, optionally in a relative date window."
    )
    parser.add_argument(
        "-s",
        "--start",
        nargs=2,
        metavar=("OFFSET", "UNIT"),
        help="Relative start date from now, e.g. -s -1 months",
    )
    parser.add_argument(
        "-e",
        "--end",
        nargs=2,
        metavar=("OFFSET", "UNIT"),
        help="Relative end date before now, e.g. -e 3 months",
    )
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = parse_args()
    try:
        resolved_start_date, resolved_end_date = resolve_relative_timeframe(
            cli_args.start, cli_args.end
        )
    except ValueError as error:
        raise SystemExit(f"Invalid date window arguments: {error}") from error

    run_daily_harvest(start_date=resolved_start_date, end_date=resolved_end_date)
