import pytest

from src.clusterer import is_agriculture_paper


@pytest.mark.parametrize(
    "title",
    [
        "Agentic AI in transforming agriculture: a review",
        "Large language models in predictive plant breeding",
        "Computer vision models for precision poultry farming",
        "3D sensing for precision weed management",
        "AI technology use in North American forestry",
    ],
)
def test_agriculture_papers_are_detected(title):
    assert is_agriculture_paper({"title": title})


def test_non_agriculture_paper_is_not_detected():
    assert not is_agriculture_paper({"title": "Self-Evolving Code-with-Image Reasoning"})


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("GNSS accuracy in forest conditions", "AI for 3F."),
        ("The effects of nearby trees on GNSS receivers", "AI for 3F."),
        ("Smartphone GNSS accuracy in forest conditions", "AI for 3F."),
        (
            "MEDQUA: A quantum adapter for medical vision-language models",
            "AI and Future of Health & Work.",
        ),
        ("Attention feature fusion for snoring detection", "AI and Future of Health & Work."),
        ("Adaptive tutoring with learning analytics", "AI in Education."),
    ],
)
def test_explicit_domain_classification(title, expected):
    from src.clusterer import detect_domain_category

    assert detect_domain_category({"title": title, "abstract": None}) == expected
