import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

def cluster_papers():
    if not os.path.exists("data/papers_raw.json"):
        return
        
    with open("data/papers_raw.json", "r") as f:
        papers = json.load(f)
        
    # Prepare text corpus (titles for simplicity; add abstracts if available)
    corpus = [p.get("title", "") for p in papers if p.get("title")]
    valid_papers = [p for p in papers if p.get("title")]
    
    if not corpus:
        return
        
    # TF-IDF Vectorization
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    X = vectorizer.fit_transform(corpus)
    
    # K-Means Clustering (Dynamic K could be implemented using Silhouette score)
    k = min(5, len(corpus))
    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = model.fit_predict(X)
    
    # Extract top terms to name clusters
    terms = vectorizer.get_feature_names_out()
    order_centroids = model.cluster_centers_.argsort()[:, ::-1]
    cluster_names = {}
    for i in range(k):
        top_terms = [terms[ind] for ind in order_centroids[i, :3]]
        cluster_names[i] = " & ".join(top_terms).title()
        
    # Assign clusters back to papers
    for i, paper in enumerate(valid_papers):
        cluster_id = int(labels[i])
        paper["cluster_id"] = cluster_id
        paper["cluster_name"] = cluster_names[cluster_id]
        
    with open("data/papers_clustered.json", "w") as f:
        json.dump(valid_papers, f, indent=2)
        
    print(f"Clustered papers into {k} groups.")

if __name__ == "__main__":
    cluster_papers()
