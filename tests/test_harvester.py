import pytest
import responses
from unittest.mock import patch
from src.harvester import fetch_batch, BASE_URL, openalex_get

@responses.activate
def test_fetch_batch_forward():
    # 1. Define the Dummy API Response
    dummy_data = {
        "results": [
            {
                "id": "https://openalex.org/W12345",
                "title": "Dummy AI Paper",
                "publication_date": "2026-11-20",
                "authorships": [{"author": {"id": "A123", "display_name": "Alan Turing"}}],
                "primary_location": {"source": {"display_name": "Nature"}}
            }
        ]
    }

    # 2. Register the Dummy API endpoint
    responses.add(
        responses.GET,
        BASE_URL,
        json=dummy_data,
        status=200
    )

    # 3. Execute the function
    papers, new_cursor = fetch_batch("2026-11-17", "forward", limit=1)

    # 4. Assert the results match the dummy data
    assert len(papers) == 1
    assert papers[0]["title"] == "Dummy AI Paper"
    assert papers[0]["venue"] == "Nature"
    assert new_cursor == "2026-11-20"

@responses.activate
@patch("src.harvester.time.sleep", return_value=None)
def test_openalex_429_retries(mock_sleep):
    responses.add(responses.GET, BASE_URL, status=429, headers={"Retry-After": "1"})
    responses.add(responses.GET, BASE_URL, json={"results": []}, status=200)

    result = openalex_get({"per-page": 1}, {"count": 0})

    assert result == {"results": []}
    assert mock_sleep.call_count == 1


def test_openalex_request_budget_exhausted():
    with patch("src.harvester.MAX_REQUESTS_PER_RUN", 1):
        with pytest.raises(RuntimeError, match="request budget exhausted"):
            openalex_get({"per-page": 1}, {"count": 1})