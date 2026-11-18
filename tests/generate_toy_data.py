import json
import os

papers = [
    {
        "id": "W1",
        "title": "jkl;jkl; — There Are Only Two Hard Problems: Cache, Naming, and Off-by-One Errors",
        "authors": [{"id": "A1", "name": "Ada J. Debugger"}],
        "uga_authors": [],
        "uga_lab": None,
        "url": "https://doi.org/10.123/1",
        "referenced_works": [],
        "cluster_name": "Foundational Computing",
        "venue": "SIGBABEL",
        "publication_date": "2026-01-14",
        "abstract": "jkl;jkl; This paper proves that every cache invalidation strategy eventually invalidates the cache invalidation strategy, and that naming remains the one function nobody can unit test.",
    },
    {
        "id": "W2",
        "title": "jkl;jkl; — The Infinite Loop: A Position Paper on Meetings",
        "authors": [{"id": "A3", "name": "Grace Stackoverflow"}],
        "uga_authors": [],
        "uga_lab": None,
        "url": "https://doi.org/10.123/2",
        "referenced_works": ["W1"],
        "cluster_name": "Foundational Computing",
        "venue": "IEEE Facepalm",
        "publication_date": "2025-11-08",
        "abstract": "jkl;jkl; We present a no-iteration meeting protocol whose only termination condition is a calendar conflict. Empirical results include unlimited synchronization overhead.",
    },
    {
        "id": "W3",
        "title": "jkl;jkl; — Attention Is All You Need, Except a Semicolon",
        "authors": [{"id": "A8", "name": "Ash Ketch-Up"}, {"id": "U1", "name": "Dr. Sarah Miller"}],
        "uga_authors": ["U1"],
        "uga_lab": "IAI Natural Language Group",
        "url": "https://arxiv.org/abs/123",
        "referenced_works": [],
        "cluster_name": "Large Language Models & NLP",
        "venue": "NeurIPSter",
        "publication_date": "2026-05-21",
        "abstract": "jkl;jkl; A transformer attends to every token except the one missing a semicolon. The resulting language model is 100% confident and 0% certain.",
    },
    {
        "id": "W4",
        "title": "jkl;jkl; — BERT but Every Layer Is a Rubber Duck",
        "authors": [
            {"id": "A9", "name": "Jacob Devlint"},
            {"id": "U1", "name": "Dr. Sarah Miller"},
        ],
        "uga_authors": ["U1"],
        "uga_lab": "IAI Natural Language Group",
        "url": "https://arxiv.org/abs/124",
        "referenced_works": ["W3"],
        "cluster_name": "Autonomous Robotics",
        "venue": "ACL: And Caffeinated LeetCode",
        "publication_date": "2026-08-09",
        "abstract": "jkl;jkl; This architecture replaces attention heads with increasingly judgmental rubber ducks. Asking the duck to explain each bug improves debugging accuracy but not the developer's dignity.",
    },
    {
        "id": "W5",
        "title": "jkl;jkl; — Sim-to-Real Transfer After the Robot Reads the README",
        "authors": [
            {"id": "U2", "name": "Dr. Marcus Vance"},
            {"id": "U3", "name": "Elena Rostova"},
        ],
        "uga_authors": ["U2", "U3"],
        "uga_lab": "UGA Robotics Dynamics Lab",
        "url": "https://doi.org/10.123/5",
        "referenced_works": [],
        "cluster_name": "Autonomous Robotics",
        "venue": "I, Robot Proceedings",
        "publication_date": "2026-03-18",
        "abstract": "jkl;jkl; We evaluate bipedal locomotion when the robot unexpectedly follows setup instructions. Its reward function converges to installing dependencies and rebooting.",
    },
    {
        "id": "W6",
        "title": "jkl;jkl; — Reinforcement Learning for Closing the Terminal on Friday",
        "authors": [{"id": "U2", "name": "Dr. Marcus Vance"}],
        "uga_authors": ["U2"],
        "uga_lab": "UGA Robotics Dynamics Lab",
        "url": "https://doi.org/10.123/6",
        "referenced_works": ["W5"],
        "cluster_name": "Autonomous Robotics",
        "venue": "SIGSTOP",
        "publication_date": "2026-09-25",
        "abstract": "jkl;jkl; An agent learns to stop training a model at the ideal time. Its final policy is Ctrl+S, git push, close laptop, and pretend the flaky test never happened.",
    },
    {
        "id": "W7",
        "title": "jkl;jkl; — AlphaFolded, Then Left in Merge Conflict",
        "authors": [{"id": "A10", "name": "John Jumper"}, {"id": "U4", "name": "Dr. Li Wei"}],
        "uga_authors": ["U4"],
        "uga_lab": "IAI Computational Biology Lab",
        "url": "https://doi.org/10.123/7",
        "referenced_works": ["W1"],
        "cluster_name": "Computational Bio-AI",
        "venue": "Nature: That's Not a Conflict",
        "publication_date": "2026-07-02",
        "abstract": "jkl;jkl; Protein structure prediction succeeds until git encounters the branches named main and master. The alpha helix refuses to choose sides.",
    },
]

old_papers = papers[:2]
new_papers = papers[2:]


def main():
    os.makedirs("data", exist_ok=True)
    with open("data/papers_old.json", "w") as f:
        json.dump(old_papers, f, indent=2)
    with open("data/papers_new.json", "w") as f:
        json.dump(new_papers, f, indent=2)
    with open("data/papers_raw.json", "w") as f:
        json.dump(papers, f, indent=2)
    print("Marked toy data generated in papers_old.json, papers_new.json, and papers_raw.json.")


if __name__ == "__main__":
    main()
