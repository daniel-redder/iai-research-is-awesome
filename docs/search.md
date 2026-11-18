# Database Search

<script>
(function () {
  var saved = localStorage.getItem('uga-theme');
  var dark = saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches);
  document.documentElement.style.backgroundColor = dark ? '#1f2430' : '#fffdf8';
  document.body.classList.add(dark ? 'uga-theme-dark' : 'uga-theme-light');
})();
</script>

<input type="text" id="db-search" placeholder="Type to filter publications..." style="width: 100%; padding: 12px; margin-bottom: 20px; font-size: 16px; border: 1px solid var(--primary-color, #ff0000); background: var(--code-bg-color, #111); color: var(--font-color, #fff); border-radius: 4px;">

<div class="search-table-wrap">
  <table id="pub-table" style="width: 100%; border-collapse: collapse; font-size: 14px; text-align: left;">
    <thead>
      <tr style="background-color: var(--primary-color, #ff0000); color: white;">
        <th style="padding: 10px; border: 1px solid #444;">Title</th>
        <th style="padding: 10px; border: 1px solid #444;">Date published</th>
        <th style="padding: 10px; border: 1px solid #444;">Conference / Venue</th>
        <th style="padding: 10px; border: 1px solid #444;">Authors</th>
        <th style="padding: 10px; border: 1px solid #444;">Lab</th>
        <th style="padding: 10px; border: 1px solid #444;">AI Domain Cluster</th>
      </tr>
    </thead>
    <tbody id="pub-tbody">
      <!-- Populated via JS -->
    </tbody>
  </table>
</div>

<script>
function normalizeName(name) {
  return String(name || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

function detailUrl(pageName, params) {
  const url = new URL(`../${pageName}/`, window.location.href);
  Object.entries(params).forEach(([key, value]) => url.searchParams.set(key, value));
  return url.href;
}

async function loadSearchData() {
  const candidates = [
    new URL('../graph_data.json', window.location.href),
    new URL('graph_data.json', window.location.href)
  ];
  for (const url of candidates) {
    try {
      const response = await fetch(url);
      if (response.ok) return response.json();
    } catch (error) {}
  }
  throw new Error('Database could not be loaded');
}

loadSearchData()
  .then(data => {
    const selectedYear = localStorage.getItem('uga-selected-year') || String(new Date().getFullYear());
    const papers = data.nodes.filter(n =>
      n.group === 'paper' &&
      typeof n.publication_date === 'string' &&
      n.publication_date.startsWith(selectedYear)
    );
    const tbody = document.getElementById('pub-tbody');
    
    function renderTable(filterText = "") {
        tbody.innerHTML = "";
        const q = filterText.toLowerCase();
        
        // Filter elements
        const filtered = papers.filter(p => {
            if (!q) return true;
            const authorStr = p.authors_raw ? p.authors_raw.map(a => a.name).join(', ') : '';
            const labStr = (p.uga_labs && p.uga_labs.length) ? p.uga_labs.join(', ') : (p.uga_lab || 'N/A');
            const clusterStr = p.cluster_name || 'Unassigned';
            const searchBlob = `${p.label} ${p.publication_date} ${p.venue} ${authorStr} ${labStr} ${clusterStr}`.toLowerCase();
            return searchBlob.includes(q);
        });

        // Slice to max 100 results for performance
        const toShow = filtered.slice(0, 100);
        
        toShow.forEach(p => {
            const ugaIds = new Set(p.uga_authors || []);
            const authorStr = p.authors_raw ? p.authors_raw.map(a => {
            const name = escapeHtml(a.name || 'Unknown');
            const href = detailUrl('author', { name: normalizeName(a.name || ''), id: a.id || '' });
            const linked = `<a href="${href}">${name}</a>`;
            return ugaIds.has(a.id) ? `<span class="uga-author-name">${linked}</span>` : linked;
            }).join(', ') : '';
          const safeDate = escapeHtml(p.publication_date || 'Unknown');
          const venue = p.venue || 'Unknown';
          const venueHref = detailUrl('venue', { name: venue });
          const safeVenue = escapeHtml(venue);
          const safeLabel = escapeHtml(p.label || 'Untitled');
          const labStr = (p.uga_labs && p.uga_labs.length) ? p.uga_labs.join(', ') : (p.uga_lab || 'N/A');
          const safeLab = escapeHtml(labStr);
          const clusterStr = p.cluster_name || 'Unassigned';
          const safeCluster = escapeHtml(clusterStr);
          const clusterHref = detailUrl('cluster', { name: clusterStr });
          const paperHref = detailUrl('paper', { id: p.id || '' });
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
          <td style="padding: 10px; border: 1px solid #444;"><a href="${paperHref}" style="color:var(--primary-color, #ff0000); text-decoration:underline; opacity:1;">${safeLabel}</a></td>
                <td style="padding: 10px; border: 1px solid #444;">${safeDate}</td>
                <td style="padding: 10px; border: 1px solid #444;"><a href="${venueHref}">${safeVenue}</a></td>
                <td style="padding: 10px; border: 1px solid #444;">${authorStr}</td>
            <td style="padding: 10px; border: 1px solid #444;">${safeLab}</td>
          <td style="padding: 10px; border: 1px solid #444;"><a href="${clusterHref}">${safeCluster}</a></td>
            `;
            tbody.appendChild(tr);
        });
        
        if (toShow.length === 0) {
          tbody.innerHTML = `<tr><td colspan="6" style="padding: 10px; text-align: center;">No results found.</td></tr>`;
        }
    }
    
    // Initial Render (Top 100)
    renderTable();
    
    // Listen for typing
    document.getElementById('db-search').addEventListener('keyup', (e) => {
        renderTable(e.target.value);
    });
  })
  .catch(err => {
    document.getElementById('pub-tbody').innerHTML = `<tr><td colspan="4" style="padding: 10px; text-align: center; color: red;">Error loading database. Ensure local server is running.</td></tr>`;
  });
</script>