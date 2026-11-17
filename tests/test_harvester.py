import pytest
import responses
import json
import os
from src.harvester import fetch_batch, BASE_URL

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