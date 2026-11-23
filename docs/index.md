# Welcome to an incomplete overview of Institute for AI research at the University of Georgia!

<section class="dashboard-card random-paper-card random-paper-hero">
  <div class="random-paper-header">
    <h2>Random Paper</h2>
    <div class="random-paper-actions">
      <button id="shuffle-paper" type="button">Shuffle</button>
      <a id="random-paper-link" href="#" class="random-paper-link">View Paper</a>
    </div>
  </div>
  <h3 id="random-paper-title">Loading…</h3>
  <p class="random-paper-meta">
    <span>Publication: <strong id="random-paper-publication-date">Loading…</strong></span>
    <span>Scan: <strong id="random-paper-scan-date">Loading…</strong></span>
  </p>
  <div class="random-paper-scroll">
    <p id="random-paper-authors" class="random-paper-authors"></p>
    <p id="random-paper-abstract"></p>
  </div>
</section>

<div class="dashboard-grid">
  <section class="dashboard-card repo-status-card database-search-card">
    <div class="database-search-summary">
      <div>
        <span class="repo-status-label">Latest Database Search</span>
        <strong id="repo-commit-date">Loading…</strong>
      </div>
      <div>
        <span class="repo-status-label">Papers published in selected year</span>
        <strong id="repo-paper-count">Loading…</strong>
      </div>
    </div>
    <div id="publication-density-chart" class="publication-density-chart" aria-label="Paper publication density by month"></div>
    <div id="density-hover-detail" class="density-hover-detail" aria-live="polite"></div>
  </section>

  <section class="dashboard-card">
    <h2>Word Frequency</h2>
    <div id="word-cloud" class="word-cloud" aria-label="Word frequency cloud"></div>
    <div id="word-paper-list" class="word-paper-list" aria-live="polite"></div>
  </section>

  <section class="dashboard-card">
    <h2>Papers by Cluster and Lab</h2>
    <div id="cluster-year-chart" class="cluster-year-chart" aria-label="Bar chart of papers by cluster"></div>
  </section>

  <section class="dashboard-card">
    <h2>Conference Publications</h2>
    <div class="venue-table-wrap">
      <table class="venue-table">
        <thead><tr><th>Conference / Venue</th><th>Papers</th></tr></thead>
        <tbody id="venue-table-body"></tbody>
      </table>
    </div>
  </section>
</div>