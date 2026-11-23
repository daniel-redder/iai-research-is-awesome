import json

from src.author_resolver import resolve_authors


def test_resolve_authors_is_idempotent_for_paper_count(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()

    papers = [
        {
            "id": "paper-1",
            "title": "Paper One",
            "authors": [
                {"id": "A1", "name": "Alice Example"},
                {"id": "A2", "name": "Bob Example"},
            ],
        },
        {
            "id": "paper-2",
            "title": "Paper Two",
            "authors": [
                {"id": "A1", "name": "Alice Example"},
            ],
        },
    ]
    roster = [
        {"normalized_name": "alice example", "status": "Fellow"},
        {"normalized_name": "bob example", "status": "Affiliate"},
    ]

    (tmp_path / "data" / "papers_raw.json").write_text(json.dumps(papers), encoding="utf-8")
    (tmp_path / "data" / "iai_roster.json").write_text(json.dumps(roster), encoding="utf-8")

    resolve_authors()
    first = json.loads((tmp_path / "data" / "authors_master.json").read_text(encoding="utf-8"))

    resolve_authors()
    second = json.loads((tmp_path / "data" / "authors_master.json").read_text(encoding="utf-8"))

    assert first == second
    assert second["A1"]["paper_count"] == 2
    assert second["A2"]["paper_count"] == 1
