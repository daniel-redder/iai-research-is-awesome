# Database Search

<input type="text" id="db-search" placeholder="Type to filter publications..." style="width: 100%; padding: 12px; margin-bottom: 20px; font-size: 16px; border: 1px solid var(--primary-color, #ff0000); background: #111; color: #fff; border-radius: 4px;">

<div style="overflow-x:auto;">
  <table id="pub-table" style="width: 100%; border-collapse: collapse; font-size: 14px; text-align: left;">
    <thead>
      <tr style="background-color: var(--primary-color, #ff0000); color: white;">
        <th style="padding: 10px; border: 1px solid #444;">Title</th>
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
fetch('graph_data.json')
  .then(response => response.json())
  .then(data => {
    const papers = data.nodes.filter(n => n.group === 'paper');
    const tbody = document.getElementById('pub-tbody');
    
    function renderTable(filterText = "") {
        tbody.innerHTML = "";
        const q = filterText.toLowerCase();
        
        // Filter elements
        const filtered = papers.filter(p => {
            if (!q) return true;
            const authorStr = p.authors_raw ? p.authors_raw.map(a => a.name).join(', ') : '';
            const labStr = p.uga_lab || 'N/A';
            const clusterStr = p.cluster_name || 'Unassigned';
            const searchBlob = `${p.label} ${authorStr} ${labStr} ${clusterStr}`.toLowerCase();
            return searchBlob.includes(q);
        });

        // Slice to max 100 results for performance
        const toShow = filtered.slice(0, 100);
        
        toShow.forEach(p => {
            const authorStr = p.authors_raw ? p.authors_raw.map(a => a.name).join(', ') : '';
            const labStr = p.uga_lab || 'N/A';
            const clusterStr = p.cluster_name || 'Unassigned';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="padding: 10px; border: 1px solid #444;"><a href="${p.url}" target="_blank" style="color:#fff; text-decoration:underline;">${p.label}</a></td>
                <td style="padding: 10px; border: 1px solid #444;">${authorStr}</td>
                <td style="padding: 10px; border: 1px solid #444;">${labStr}</td>
                <td style="padding: 10px; border: 1px solid #444;">${clusterStr}</td>
            `;
            tbody.appendChild(tr);
        });
        
        if (toShow.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="padding: 10px; text-align: center;">No results found.</td></tr>`;
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