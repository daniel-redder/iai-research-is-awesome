# IAI Research is Awesome!

![Last Updated](https://img.shields.io/badge/Last_Updated-2026--11--17-blue)
![Breadth](https://img.shields.io/badge/Breadth-2026--10--15_to_2026--11--17-green)
## Architecture

This repository runs automatically via GitHub Actions:
1. **Harvester (`src/harvester.py`)**: Polls OpenAlex for paper metadata (titles, venues, citations, authors, dates).
2. **Author Resolver (`src/author_resolver.py`)**: Deduplicates authors and tags them as Core, Affiliate, Student, or Uncertain.
3. **Clusterer (`src/clusterer.py`)**: Uses TF-IDF and K-Means to cluster papers by textual similarity and generates dynamic cluster names.
4. **Graph Builder (`src/graph_builder.py`)**: Formats the clustered data into a node/edge JSON graph.
5. **Cosmograph Frontend (`docs/index.html`)**: Renders a high-performance webGL network graph on GitHub Pages.

## Setup Instructions

1. Push this repository to GitHub.
2. Enable **GitHub Pages** in your repository settings (Settings > Pages) and point it to the `/docs` folder on the `main` branch.
3. The GitHub Action will run automatically every Monday to update the dataset and graph.

## Harvester Timeframe Arguments

You can run the harvester with a relative publication-date window:

- `-e OFFSET UNIT`: End date relative to now as `now - OFFSET`.
- `-s OFFSET UNIT`: Start date relative to now as `now + OFFSET`.

Examples:

- `python src/harvester.py -e 3 months` searches up to 3 months before today.
- `python src/harvester.py -s -1 months` starts searching 1 month before today.
