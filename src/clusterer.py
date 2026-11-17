import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

def generate_copilot_cluster_name(tfidf_matrix, vectorizer, cluster_indices):
    """Simulates an LLM/Copilot API generating a semantic cluster name based on keywords."""
    cluster_center = np.asarray(tfidf_matrix[cluster_indices].mean(axis=0)).flatten()
    top_indices = np.argsort(cluster_center)[-3:]
    words = [vectorizer.get_feature_names_out()[i] for i in reversed(top_indices)]
    
    # Simulate LLM Prompt Logic mapped to our AI domains
    if "transformer" in words or "language" in words or "bert" in words: return "Large Language Models & NLP"
    if "bipedal" in words or "manipulation" in words or "locomotion" in words: return "Autonomous Robotics"
    if "protein" in words or "alphafold" in words or "structure" in words: return "Computational Bio-AI"
    if "turing" in words or "edvac" in words: return "Foundational Computing"
    
    return f"{words[0].capitalize()} & {words[1].capitalize()} AI"

def run_clustering():
    with open("data/papers_old.json", "r") as f: old_data = json.load(f)
    with open("data/papers_new.json", "r") as f: new_data = json.load(f)

    all_papers = old_data + new_data
    titles = [p["title"] for p in all_papers]

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(titles)

    old_clusters = {}
    for i, p in enumerate(old_data):
        c_name = p.get("cluster_name")
        if c_name not in old_clusters: old_clusters[c_name] = []
        old_clusters[c_name].append(i)

    centroids = {c: np.asarray(tfidf_matrix[i].mean(axis=0)) for c, i in old_clusters.items()}

    unassigned_indices = []
    for idx in range(len(old_data), len(all_papers)):
        vec = tfidf_matrix[idx]
        best_match, max_sim = None, 0.0
        for c_name, centroid in centroids.items():
            sim = cosine_similarity(vec, centroid)[0][0]
            if sim > max_sim:
                max_sim = sim; best_match = c_name

        if max_sim > 0.15:
            all_papers[idx]["cluster_name"] = best_match
        else:
            unassigned_indices.append(idx)

    if unassigned_indices:
        unassigned_matrix = tfidf_matrix[unassigned_indices]
        k = min(3, len(unassigned_indices)) # Force multiple clusters for our demo
        kmeans = KMeans(n_clusters=k, random_state=42).fit(unassigned_matrix)
        
        for cluster_id in range(k):
            local_indices = np.where(kmeans.labels_ == cluster_id)[0]
            global_indices = [unassigned_indices[i] for i in local_indices]
            # Call our simulated Copilot API
            new_cluster_name = generate_copilot_cluster_name(tfidf_matrix, vectorizer, global_indices)
            for g_idx in global_indices:
                all_papers[g_idx]["cluster_name"] = new_cluster_name

    with open("data/papers_raw.json", "w") as f: json.dump(all_papers, f, indent=2)
    print("Semantic AI clustering complete.")

if __name__ == "__main__":
    run_clustering()