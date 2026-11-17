# Welcome to an incomplete overview of Institute for AI research at the University of Georgia!

This tool queries the OpenAlex database to collate research published by faculty/affiliates/core member of the institute for artificial intelligence. This database updates every day. If you find an incorrect or missing listing please submit an issue on this repository.

On this page, I show cool summary plots over AI research at UGA. Specific papers can be found through **search** or via the **graph** explorer.

I made this tool for IAI's use, but it is not officially sponsored or endorsed by them. Look on Google Scholar, Open Alex, or lab websites directly for more up-to-date information.



<!-- <iframe id="graph-frame" src="graph_app.html" width="100%" height="600px" style="border:1px solid #e8eaed; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"></iframe>  -->

----

<div class="repo-status-grid">
  <div class="repo-status-card database-search-card">
    <div class="database-search-summary">
      <div>
        <span class="repo-status-label">Latest Database Search</span>
        <strong id="repo-commit-date">2026-11-17</strong>
      </div>
      <div>
        <span class="repo-status-label">Papers logged</span>
        <strong id="repo-paper-count">Loading…</strong>
      </div>
    </div>
    <div id="publication-density-chart" class="publication-density-chart" aria-label="Paper publication density by month"></div>
    <div id="density-hover-detail" class="density-hover-detail" aria-live="polite"></div>
  </div>
</div>

<div class="dashboard-grid">
  <section class="dashboard-card">
    <h2>Word Frequency</h2>
    <div id="word-cloud" class="word-cloud" aria-label="Word frequency cloud"></div>
    <div id="word-paper-list" class="word-paper-list" aria-live="polite"></div>
  </section>

  <section class="dashboard-card">
    <h2>Papers by Cluster and Year</h2>
    <div class="year-chart-controls">
      <button id="year-chart-prev" type="button" aria-label="Previous year">&lt;</button>
      <strong id="year-chart-title"></strong>
      <button id="year-chart-next" type="button" aria-label="Next year">&gt;</button>
    </div>
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

  <section class="dashboard-card random-paper-card">
    <div class="random-paper-header">
      <h2>Random Paper</h2>
      <div class="random-paper-actions">
        <button id="shuffle-paper" type="button">Shuffle</button>
        <a id="random-paper-link" href="#" target="_blank" rel="noopener" class="random-paper-link">View Paper</a>
      </div>
    </div>
    <h3 id="random-paper-title">Loading…</h3>
    <p id="random-paper-authors" class="random-paper-authors"></p>
    <p id="random-paper-abstract"></p>
  </section>
</div>