import json
import os

toy_papers = [
    {
        "id": "W1", "title": "On Computable Numbers (Turing Machine)",
        "authors": [{"id": "A1", "name": "Alan Turing"}],
        "referenced_works": []
    },
    {
        "id": "W2", "title": "Computing Machinery and Intelligence",
        "authors": [{"id": "A1", "name": "Alan Turing"}],
        "referenced_works": ["W1"]
    },
    {
        "id": "W3", "title": "A Logical Calculus of Nervous Activity",
        "authors": [{"id": "A2", "name": "Warren McCulloch"}, {"id": "A3", "name": "Walter Pitts"}],
        "referenced_works": ["W1"]
    },
    {
        "id": "W4", "title": "The Perceptron: A Probabilistic Model",
        "authors": [{"id": "A4", "name": "Frank Rosenblatt"}],
        "referenced_works": ["W3", "W1"]
    },
    {
        "id": "W5", "title": "Learning by Back-Propagating Errors",
        "authors": [{"id": "A5", "name": "Geoffrey Hinton"}, {"id": "A6", "name": "David Rumelhart"}],
        "referenced_works": ["W4"]
    },
    {
        "id": "W6", "title": "Deep Learning for Vision",
        "authors": [{"id": "A5", "name": "Geoffrey Hinton"}, {"id": "A7", "name": "Yann LeCun"}],
        "referenced_works": ["W5", "W4"]
    },
    {
        "id": "W7", "title": "Attention Is All You Need",
        "authors": [{"id": "A8", "name": "Ashish Vaswani"}],
        "referenced_works": ["W5"]
    },
    {
        "id": "W8", "title": "BERT: Deep Bidirectional Transformers",
        "authors": [{"id": "A9", "name": "Jacob Devlin"}],
        "referenced_works": ["W7", "W5"]
    }
]

def main():
    os.makedirs("data", exist_ok=True)
    with open("data/papers_raw.json", "w") as f:
        json.dump(toy_papers, f, indent=2)
    print("Rich toy data generated at data/papers_raw.json!")

if __name__ == "__main__":
    main()