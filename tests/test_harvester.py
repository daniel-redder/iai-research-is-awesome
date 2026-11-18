from datetime import UTC, datetime
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
import responses

from src.harvester import (
    BASE_URL,
    fetch_batch,
    openalex_get,
    resolve_relative_timeframe,
)


@responses.activate
def test_fetch_batch_forward():
    # 1. Define the Dummy API Response
    dummy_data = {
        "results": [
            {
                "id": "https://openalex.org/W12345",
                "title": "Dummy AI Paper",
                "publication_date": "2026-11-20",
                "authorships": [{"author": {"id": "A123", "display_name": "Tianming Liu"}}],
                "primary_location": {"source": {"display_name": "Nature"}},
            }
        ]
    }

    # 2. Register the Dummy API endpoint
    responses.add(responses.GET, BASE_URL, json=dummy_data, status=200)

    # 3. Execute the function
    papers, new_cursor = fetch_batch("2026-11-17", "forward", limit=1)

    # 4. Assert the results match the dummy data
    assert len(papers) == 1
    assert papers[0]["title"] == "Dummy AI Paper"
    assert papers[0]["venue"] == "Nature"
    assert new_cursor == "2026-11-20"


@responses.activate
@patch("src.harvester.time.sleep", return_value=None)
def test_openalex_429_retries(mock_sleep, capsys):
    responses.add(responses.GET, BASE_URL, status=429, headers={"Retry-After": "1"})
    responses.add(responses.GET, BASE_URL, json={"results": []}, status=200)

    result = openalex_get({"per-page": 1}, {"count": 0}, {"count": 0})
    captured = capsys.readouterr()

    assert result == {"results": []}
    assert mock_sleep.call_count == 1
    assert "DEBUG OpenAlexBackoff status_code=429" in captured.out


def test_openalex_request_budget_exhausted():
    with patch("src.harvester.MAX_REQUESTS_PER_RUN", 1):
        with pytest.raises(RuntimeError, match="request budget exhausted"):
            openalex_get({"per-page": 1}, {"count": 1})


@responses.activate
@patch("src.harvester.time.sleep", return_value=None)
def test_openalex_failed_request_budget_exhausted(mock_sleep):
    responses.add(responses.GET, BASE_URL, status=500)

    with patch("src.harvester.MAX_FAILED_REQUESTS_PER_RUN", 1):
        with pytest.raises(RuntimeError, match="failed request budget exhausted"):
            openalex_get({"per-page": 1}, {"count": 0}, {"count": 0})

    assert mock_sleep.call_count == 1


def test_resolve_relative_timeframe_month_examples():
    now = datetime(2026, 11, 17, tzinfo=UTC)

    start_date, _ = resolve_relative_timeframe(["-1", "months"], None, now)
    _, end_date = resolve_relative_timeframe(None, ["3", "months"], now)

    assert start_date == "2026-10-17"
    assert end_date == "2026-08-17"


def test_resolve_relative_timeframe_rejects_inverted_window():
    now = datetime(2026, 11, 17, tzinfo=UTC)

    with pytest.raises(ValueError, match="after end date"):
        resolve_relative_timeframe(["-1", "months"], ["3", "months"], now)


@responses.activate
def test_fetch_batch_forward_with_upper_bound_filter():
    responses.add(responses.GET, BASE_URL, json={"results": []}, status=200)

    fetch_batch(
        "2026-10-01",
        "forward",
        limit=1,
        upper_bound_date="2026-10-31",
    )

    request_url = responses.calls[0].request.url
    query_params = parse_qs(urlparse(request_url).query)
    filter_value = query_params["filter"][0]

    assert "from_publication_date:2026-10-01" in filter_value
    assert "to_publication_date:2026-10-31" in filter_value
