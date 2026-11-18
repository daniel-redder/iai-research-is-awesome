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
    assert not is_agriculture_paper(
        {"title": "Self-Evolving Code-with-Image Reasoning"})
