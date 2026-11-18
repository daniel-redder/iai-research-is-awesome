import pytest

from src.lab_resolver import clean_lab_name, extract_labs, uga_lab_name


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("& Events Resources Contact Directory Directory Institute", "Uncertain"),
        ("For Fellows For Industry Contact Directory Institute", "Uncertain"),
        ("Office 155G Riverbend Research Lab", "Uncertain"),
        ("00am Seminar on AI at the Center", "Uncertain"),
        ("Director of the Institute", "Uncertain"),
        ("His lab", "Uncertain"),
        (
            "commercially relevant sustainable materials The Hoarfrost lab",
            "The Hoarfrost Lab",
        ),
        ("and the Small Satellite Research Laboratory", "The Small Satellite Research Laboratory"),
    ],
)
def test_clean_lab_name(value, expected):
    assert clean_lab_name(value) == expected


def test_extract_labs_returns_uncertain_when_no_name_is_found():
    assert extract_labs({"name": "Example Person", "title": "Professor", "profile_url": ""}) == [
        "Uncertain"
    ]


def test_extract_labs_keeps_named_lab_and_discards_uncertain_fragments():
    person = {
        "name": "Example Person",
        "title": "The Hoarfrost Lab",
        "profile_url": "",
    }

    assert extract_labs(person) == ["The Hoarfrost Lab"]


def test_uga_lab_name_excludes_external_and_uncertain_names():
    assert uga_lab_name("The Hoarfrost Lab") == "The Hoarfrost Lab"
    assert uga_lab_name("THINC Lab") == "THINC Lab"
    assert uga_lab_name("UGA Small Satellite Research Laboratory") == (
        "The Small Satellite Research Laboratory"
    )
    assert uga_lab_name("The Indian Institute") is None
    assert uga_lab_name("Uncertain") is None
