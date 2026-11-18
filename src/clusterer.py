import json
import os
import re

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

RESEARCH_CATEGORIES = {
    "Foundational AI.": (
        "core computational mathematical theoretical principles machine learning "
        "reasoning perception "
        "autonomous systems optimization algorithms representation learning probabilistic modeling"
    ),
    "AI and Future of Health & Work.": (
        "medical informatics clinical decision support healthcare diagnostics patient outcomes "
        "hospital health labor economics productivity workplace automation human performance"
    ),
    "AI for 3F.": (
        "food fuel fiber precision agriculture crop livestock forestry agronomy soil irrigation "
        "supply chains bioenergy sustainable farming"
    ),
    "AI for Cyber & Societal Security.": (
        "cybersecurity threat detection intrusion malware adversarial defense privacy "
        "critical infrastructure resilience public safety risk assessment"
    ),
    "AI in Education.": (
        "intelligent tutoring educational data mining learning analytics adaptive learning "
        "classroom pedagogy student outcomes STEM instruction"
    ),
    "Ethics of AI for Human Society.": (
        "fairness accountability transparency explainability bias governance responsible ai "
        "trust autonomy ethics societal impact"
    ),
}

FOUNDATIONAL_CATEGORY = "Foundational AI."
AGRICULTURE_CATEGORY = "AI for 3F."
FOUNDATIONAL_PRIOR = 0.9
DOMAIN_PREFERENCE_MARGIN = 0.03
MAX_TEXT_FIELD_LEN = 4000
MAX_ABSTRACT_TOKENS = 12000
MAX_ABSTRACT_POSITION = 50000
AGRICULTURE_TITLE_PATTERN = re.compile(
    r"\b(?:agricultur\w*|agronom\w*|crops?|cropping|farms?|farming|poultry|"
    r"broilers?|chickens?|livestock|cattle|piglets?|forestr\w*|timberland|"
    r"alfalfa|cotton|irrigation|horticulture|aquaculture|aquaponics|dairy|"
    r"agri[- ]food|food production|weed (?:management|control)|"
    r"plant (?:breeding|phenotyping|protein|disease|health|growth))\b",
    re.IGNORECASE,
)


def safe_text(value, max_len=MAX_TEXT_FIELD_LEN):
    text = value if isinstance(value, str) else ""
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    return text.strip()[:max_len]


def safe_cluster_name(value):
    name = safe_text(value, max_len=128)
    if not name:
        return None
    # Collapse excessive whitespace to keep cluster labels stable.
    return re.sub(r"\s+", " ", name)


def abstract_to_text(abstract):
    """Convert OpenAlex-style abstract inverted index or plain text into readable text."""
    if isinstance(abstract, str):
        return safe_text(abstract)
    if not isinstance(abstract, dict) or not abstract:
        return ""

    valid_positions = []
    token_positions = {}
    seen_positions = 0

    for token, positions in abstract.items():
        safe_token = safe_text(token, max_len=80)
        if not safe_token or not isinstance(positions, list):
            continue
        for pos in positions:
            if seen_positions >= MAX_ABSTRACT_TOKENS:
                break
            if isinstance(pos, int) and 0 <= pos <= MAX_ABSTRACT_POSITION:
                token_positions.setdefault(safe_token, []).append(pos)
                valid_positions.append(pos)
                seen_positions += 1
        if seen_positions >= MAX_ABSTRACT_TOKENS:
            break

    max_position = max(valid_positions, default=-1)
    if max_position < 0:
        return ""

    tokens = [""] * (max_position + 1)
    for word, positions in token_positions.items():
        for pos in positions:
            if 0 <= pos <= max_position:
                tokens[pos] = word
    return safe_text(" ".join(token for token in tokens if token), max_len=MAX_TEXT_FIELD_LEN)


def paper_text(paper):
    if not isinstance(paper, dict):
        return ""
    title = safe_text(paper.get("title", ""))
    abstract = abstract_to_text(paper.get("abstract", ""))
    return f"{title} {abstract}".strip()


def is_agriculture_paper(paper):
    """Detect clear agriculture, food, livestock, and forestry work from its title."""
    if not isinstance(paper, dict):
        return False
    return bool(AGRICULTURE_TITLE_PATTERN.search(safe_text(paper.get("title", ""))))


def generate_copilot_cluster_name(tfidf_matrix, vectorizer, cluster_indices):
    """Assign a cluster while preferring domain categories over Foundational AI when close."""
    if not cluster_indices:
        return FOUNDATIONAL_CATEGORY

    cluster_center = np.asarray(tfidf_matrix[cluster_indices].mean(axis=0))
    category_names = list(RESEARCH_CATEGORIES.keys())
    category_texts = list(RESEARCH_CATEGORIES.values())
    category_matrix = vectorizer.transform(category_texts)

    similarities = cosine_similarity(cluster_center, category_matrix).ravel()
    scores = dict(zip(category_names, similarities, strict=True))

    foundational_score = scores.get(FOUNDATIONAL_CATEGORY, 0.0) * FOUNDATIONAL_PRIOR
    domain_scores = {k: v for k, v in scores.items() if k != FOUNDATIONAL_CATEGORY}

    if not domain_scores:
        return FOUNDATIONAL_CATEGORY

    best_domain, best_domain_score = max(domain_scores.items(), key=lambda item: item[1])

    # Prefer domain-specific categories unless Foundational is clearly stronger.
    if best_domain_score >= foundational_score - DOMAIN_PREFERENCE_MARGIN:
        return best_domain
    return FOUNDATIONAL_CATEGORY


def run_clustering():
    old_path = "data/papers_old.json"
    new_path = "data/papers_new.json"
    raw_path = "data/papers_raw.json"

    if os.path.exists(old_path):
        with open(old_path) as f:
            old_data = json.load(f)
        if not isinstance(old_data, list):
            old_data = []
    else:
        old_data = []

    if os.path.exists(new_path):
        with open(new_path) as f:
            new_data = json.load(f)
        if not isinstance(new_data, list):
            new_data = []
    elif os.path.exists(raw_path):
        # Non-test mode: operate directly on the existing raw paper set.
        with open(raw_path) as f:
            new_data = json.load(f)
        if not isinstance(new_data, list):
            new_data = []
    else:
        raise FileNotFoundError(
            "Expected one of data/papers_new.json or data/papers_raw.json for clustering input."
        )

    old_data = [paper for paper in old_data if isinstance(paper, dict)]
    new_data = [paper for paper in new_data if isinstance(paper, dict)]

    all_papers = old_data + new_data
    if not all_papers:
        with open("data/papers_raw.json", "w") as f:
            json.dump([], f, indent=2)
        print("No papers to cluster.")
        return

    corpus = [paper_text(p) for p in all_papers]

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = csr_matrix(vectorizer.fit_transform(corpus))

    old_clusters = {}
    for i, p in enumerate(old_data):
        c_name = safe_cluster_name(p.get("cluster_name"))
        if c_name:
            p["cluster_name"] = c_name
        if c_name not in old_clusters:
            old_clusters[c_name] = []
        old_clusters[c_name].append(i)

    old_clusters = {name: idxs for name, idxs in old_clusters.items() if name}

    centroids = {c: np.asarray(tfidf_matrix[i].mean(axis=0)) for c, i in old_clusters.items()}

    unassigned_indices = []
    for idx in range(len(old_data), len(all_papers)):
        vec = tfidf_matrix[idx]
        best_match, max_sim = None, 0.0
        for c_name, centroid in centroids.items():
            sim = cosine_similarity(vec, centroid)[0][0]
            if sim > max_sim:
                max_sim = sim
                best_match = c_name

        if max_sim > 0.15:
            all_papers[idx]["cluster_name"] = best_match
        else:
            unassigned_indices.append(idx)

    if unassigned_indices:
        unassigned_matrix = tfidf_matrix[unassigned_indices]
        # Force multiple clusters for our demo
        k = min(3, len(unassigned_indices))
        kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto").fit(unassigned_matrix)

        for cluster_id in range(k):
            local_indices = np.where(kmeans.labels_ == cluster_id)[0]
            global_indices = [unassigned_indices[i] for i in local_indices]
            # Call our simulated Copilot API
            new_cluster_name = generate_copilot_cluster_name(
                tfidf_matrix, vectorizer, global_indices
            )
            for g_idx in global_indices:
                all_papers[g_idx]["cluster_name"] = new_cluster_name

    for paper in all_papers:
        if is_agriculture_paper(paper):
            paper["cluster_name"] = AGRICULTURE_CATEGORY

    with open("data/papers_raw.json", "w") as f:
        json.dump(all_papers, f, indent=2)
    print("Semantic AI clustering complete.")


if __name__ == "__main__":
    run_clustering()
