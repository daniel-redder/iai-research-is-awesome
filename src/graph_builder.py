import json
import os
import re
from urllib.parse import urlparse


def normalize_name(name):
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


MAX_TEXT_LEN = 2000
MAX_ABSTRACT_TERMS = 10000
MAX_ABSTRACT_POSITION = 50000
MAX_AUTHORS_PER_PAPER = 300
MAX_REFS_PER_PAPER = 3000


def safe_text(value, max_len=MAX_TEXT_LEN):
    text = value if isinstance(value, str) else ""
    text = "".join(ch for ch in text if ch ==
                   "\n" or ch == "\t" or ord(ch) >= 32)
    return text.strip()[:max_len]


def safe_identifier(value, max_len=256):
    identifier = safe_text(value, max_len=max_len)
    return identifier or None


def safe_url(value):
    text = safe_text(value, max_len=2048)
    if not text:
        return None
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return text
    return None


def safe_date(value):
    date_text = safe_text(value, max_len=32)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_text):
        return date_text
    return None


def sanitize_abstract(index):
    if isinstance(index, str):
        return safe_text(index, max_len=8000)
    if not isinstance(index, dict):
        return {}

    cleaned = {}
    kept = 0
    for token, positions in index.items():
        if kept >= MAX_ABSTRACT_TERMS:
            break
        safe_token = safe_text(token, max_len=80)
        if not safe_token or not isinstance(positions, list):
            continue

        safe_positions = []
        for pos in positions:
            if kept >= MAX_ABSTRACT_TERMS:
                break
            if isinstance(pos, int) and 0 <= pos <= MAX_ABSTRACT_POSITION:
                safe_positions.append(pos)
                kept += 1
        if safe_positions:
            cleaned[safe_token] = safe_positions

    return cleaned


def sanitize_author_list(authors):
    if not isinstance(authors, list):
        return []
    sanitized = []
    for author in authors[:MAX_AUTHORS_PER_PAPER]:
        if not isinstance(author, dict):
            continue
        author_id = safe_identifier(author.get("id"))
        author_name = safe_text(author.get(
            "name"), max_len=200) or "Unknown author"
        sanitized.append({"id": author_id, "name": author_name})
    return sanitized


def sanitize_reference_list(references):
    if not isinstance(references, list):
        return []
    sanitized = []
    seen = set()
    for ref in references[:MAX_REFS_PER_PAPER]:
        ref_id = safe_identifier(ref)
        if ref_id and ref_id not in seen:
            seen.add(ref_id)
            sanitized.append(ref_id)
    return sanitized


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5, viewport-fit=cover">
    <title>IAI Research Explorer</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script src="javascripts/graph-gpu.js"></script>
    <style>
        :root {
            --g-bg: #f8f9fa;
            --g-text: #202124;
            --g-header-bg: #ffffff;
            --g-header-text: #202124;
            --g-border: #d9dce2;
            --g-btn-primary: #ba0c2f;
            --g-btn-primary-hover: #960925;
            --g-btn-secondary: #5f6368;
            --g-btn-secondary-hover: #3c4043;
            --g-panel-bg: #ffffff;
            --g-panel-text: #202124;
            --g-tooltip-bg: rgba(255, 255, 255, 0.98);
            --g-tooltip-text: #202124;
            --g-hint-bg: rgba(0, 0, 0, 0.7);
            --g-hint-text: #ffffff;
        }
        body.graph-dark {
            --g-bg: #1f2430;
            --g-text: #f4f1ea;
            --g-header-bg: #222838;
            --g-header-text: #f4f1ea;
            --g-border: #41475a;
            --g-btn-primary: #d3234a;
            --g-btn-primary-hover: #ba0c2f;
            --g-btn-secondary: #3b4256;
            --g-btn-secondary-hover: #4c5670;
            --g-panel-bg: #2a3040;
            --g-panel-text: #f4f1ea;
            --g-tooltip-bg: rgba(42, 48, 64, 0.97);
            --g-tooltip-text: #f4f1ea;
            --g-hint-bg: rgba(26, 30, 40, 0.86);
            --g-hint-text: #f4f1ea;
        }
        body, html { margin: 0; padding: 0; height: 100%; font-family: 'Courier New', Courier, monospace; overflow: hidden; background: var(--g-bg); color: var(--g-text); }
        #network { width: 100%; height: 100%; }
        
        #header-bar { 
            position: absolute; top: 0; left: 0; width: 100%; 
            background: var(--g-header-bg); border-bottom: 2px solid var(--g-btn-primary); padding: 12px 20px; 
            box-sizing: border-box; font-size: 14px; z-index: 20; 
            display: flex; justify-content: space-between; align-items: center; 
            min-height: 60px; 
        }
        #header-info { flex-grow: 1; color: var(--g-header-text); }
        #header-info a { color: #ff4444; text-decoration: underline; font-weight: bold; margin-left: 15px; }
        .uga-author-red { color: #ff0000; font-weight: bold; }
        
        #header-controls { display: flex; gap: 3px; align-items: center; flex-wrap: wrap; }
        button {
            width: 148px;
            min-height: 36px;
            padding: 8px 12px;
            background: var(--g-btn-primary);
            color: #fff;
            border: 1px solid transparent;
            border-radius: 4px;
            cursor: pointer;
            font-family: inherit;
            font-weight: bold;
            font-size: 13px;
            transition: all 0.2s;
        }
        button:hover { background: var(--g-btn-primary-hover); }
        button.secondary { background: var(--g-btn-secondary); }
        button.secondary:hover { background: var(--g-btn-secondary-hover); }
        #btn-reset { background: #550000; border-color: #ff0000; }
        
        #settings-panel {
            display: none; position: absolute; top: 70px; right: 20px; 
            background: var(--g-panel-bg); color: var(--g-panel-text); padding: 15px; border-radius: 0; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.5); z-index: 30; width: 280px; 
            border: 1px solid var(--g-btn-primary);
        }
        .setting-row { margin-bottom: 15px; }
        .setting-row label { display: block; font-size: 12px; font-weight: bold; margin-bottom: 5px; color: var(--g-panel-text);}
        .setting-row input { width: 100%; accent-color: var(--g-btn-primary); }
        
        #custom-tooltip {
            position: absolute; display: none; background: var(--g-tooltip-bg);
            border: 1px solid var(--g-btn-primary); padding: 12px; font-size: 13px;
            color: var(--g-tooltip-text); z-index: 100; pointer-events: auto; max-width: 320px; line-height: 1.4;
        }
        #custom-tooltip a { color: #ff0000; text-decoration: underline; }

        #search-modal { display: none; position: absolute; top: 70px; left: 20px; background: var(--g-panel-bg); color: var(--g-panel-text); padding: 15px; border: 1px solid var(--g-btn-primary); z-index: 30; width: 300px; }
        #search-modal input { width: 100%; padding: 8px; box-sizing: border-box; margin-bottom: 10px; background: var(--g-bg); border: 1px solid var(--g-border); color: var(--g-text); }
        #search-results { max-height: 200px; overflow-y: auto; font-size: 13px; }
        .search-item { padding: 8px; border-bottom: 1px solid #333; cursor: pointer; }
        .search-item:hover { background: #ff0000; color: #000; }
        .search-hint { position: absolute; bottom: 20px; left: 20px; background: var(--g-hint-bg); border: 1px solid var(--g-border); color: var(--g-hint-text); padding: 5px 10px; font-size: 12px; z-index: 10; pointer-events: none;}
        @media (max-width: 760px) {
            body, html { min-height: 100%; }
            #header-bar { min-height: 48px; height: auto; max-height: 56px; overflow: hidden; padding: 6px; align-items: flex-start; }
            #header-info { display: none; }
            #header-controls { width: 100%; gap: 6px; }
            #header-controls button { width: auto; min-width: 34px; flex: 1 1 14%; min-height: 34px; padding: 4px 2px; font-size: 8.5px; line-height: 1.05; }
            #header-controls #btn-theme, #header-controls #btn-settings, #header-controls #btn-fullscreen { flex: 0 1 auto; }
            #settings-panel, #search-modal { top: 52px; left: 8px; right: 8px; width: auto; max-height: calc(100vh - 60px); overflow-y: auto; }
            #custom-tooltip { max-width: calc(100vw - 24px); }
            .search-hint { display: none; }
        }
        @media (max-width: 420px) {
            #header-controls button { flex-basis: 28%; }
            #header-controls #btn-reset, #header-controls #btn-fullscreen { display: none; }
        }
        @media (max-width: 340px) {
            #header-controls button { flex-basis: 14%; min-width: 30px; font-size: 8px; }
            #header-controls #btn-reset { display: none; }
        }
    </style>
</head>
<body>
    <div id="header-bar">
        <div id="header-info"><i>Select a node or use Ctrl+F to search the IAI database...</i></div>
        
        <div id="header-controls">
            <button id="btn-paper">Citations</button>
            <button id="btn-cluster">Clusters</button>
            <button id="btn-labs">Labs</button>
            <button id="btn-author">Authors</button>
            <button id="btn-reset" style="display:none;">Reset View</button>
            <div style="width: 1px; height: 30px; background: #555; margin: 0 5px;"></div>
            <button id="btn-theme" class="secondary">☾ Dark</button>
            <button id="btn-settings">⚙️ Physics</button>
            <button id="btn-fullscreen">⛶ Fullscreen</button>
        </div>
    </div>
    
    <div id="settings-panel">
        <h3 style="margin:0 0 10px 0; font-size:14px; color:#ff0000;">Graph Physics</h3>
        <div class="setting-row">
            <label><input type="checkbox" id="inp-enable-physics"> Enable physics</label>
        </div>
        <div class="setting-row">
            <label>Node Gravity (<span id="val-gravity"></span>)</label>
            <input type="range" id="inp-gravity" min="-8000" max="-500" step="100">
        </div>
        <div class="setting-row">
            <label>Spring Length (<span id="val-spring"></span>)</label>
            <input type="range" id="inp-spring" min="50" max="400" step="10">
        </div>
        <button id="btn-save-settings" style="width:100%; margin-top:5px; background:#ff0000; color:#000;">Save to Browser</button>
    </div>
    
    <div id="search-modal">
        <h3 style="margin:0 0 10px 0; font-size:14px; color:#ff0000;">Fuzzy Search</h3>
        <input type="text" id="search-input" placeholder="Search title, author, lab...">
        <div id="search-results"></div>
    </div>
    
    <div class="search-hint">Press <b>Ctrl+F</b> to search</div>
    <div id="custom-tooltip"></div>
    <div id="network"></div>
    <canvas id="gpu-network" aria-label="GPU-accelerated research graph"></canvas>

    <script>
        let allNodes = []; let allEdges = [];
        let network = null; let currentMode = 'paper';
        let hasInitialFit = false;
        const clusterColors = ["#ff0000", "#1a73e8", "#fbbc04", "#34a853", "#8e24aa", "#ff6d00"];
        let clusterMap = {}; let labMap = {}; let colorIndex = 0; let labColorIndex = 0;
        const tooltip = document.getElementById('custom-tooltip');
        let tooltipAnchor = { x: 0, y: 0 };
        let tooltipHideTimer = null;

        function hideTooltip() {
            clearTimeout(tooltipHideTimer);
            tooltip.style.display = 'none';
            tooltip.innerHTML = '';
        }

        function scheduleTooltipHide() {
            clearTimeout(tooltipHideTimer);
            tooltipHideTimer = setTimeout(function () {
                if (!tooltip.matches(':hover')) hideTooltip();
            }, 120);
        }

        tooltip.addEventListener('mouseenter', function () { clearTimeout(tooltipHideTimer); });
        tooltip.addEventListener('mouseleave', hideTooltip);

        document.addEventListener('mousemove', function(e) {
            tooltipAnchor = { x: e.pageX + 15, y: e.pageY + 15 };
            if (tooltip.style.display === 'block' && !tooltip.matches(':hover')) {
                tooltip.style.left = tooltipAnchor.x + 'px';
                tooltip.style.top = tooltipAnchor.y + 'px';
            }
        });

        // PHYSICS PARAMS
        let currentGravity = -3000;
        let currentSpring = 150;
        let physicsEnabled = localStorage.getItem('iai_graph_physics_enabled') === 'true';
        document.getElementById('inp-enable-physics').checked = physicsEnabled;
        
        if (localStorage.getItem('iai_graph_gravity')) currentGravity = parseInt(localStorage.getItem('iai_graph_gravity'));
        if (localStorage.getItem('iai_graph_spring')) currentSpring = parseInt(localStorage.getItem('iai_graph_spring'));
        
        document.getElementById('inp-gravity').value = currentGravity;
        document.getElementById('inp-spring').value = currentSpring;
        
        document.getElementById('val-gravity').innerText = currentGravity;
        document.getElementById('val-spring').innerText = currentSpring;

        document.getElementById('inp-gravity').oninput = (e) => { currentGravity = parseInt(e.target.value); document.getElementById('val-gravity').innerText = currentGravity; if(network) applyPhysics(); };
        document.getElementById('inp-spring').oninput = (e) => { currentSpring = parseInt(e.target.value); document.getElementById('val-spring').innerText = currentSpring; if(network) applyPhysics(); };

        document.getElementById('btn-settings').onclick = () => {
            const p = document.getElementById('settings-panel');
            p.style.display = p.style.display === 'block' ? 'none' : 'block';
        };
        document.getElementById('btn-save-settings').onclick = () => {
            localStorage.setItem('iai_graph_gravity', currentGravity);
            localStorage.setItem('iai_graph_spring', currentSpring);
            localStorage.setItem('iai_graph_physics_enabled', physicsEnabled);
            document.getElementById('settings-panel').style.display = 'none';
        };

        // Theme toggle defaults to system preference until user sets a choice.
        const THEME_KEY = 'iai_graph_theme';
        const systemPrefersDark = () => window.matchMedia('(prefers-color-scheme: dark)').matches;
        function activeTheme() {
            const saved = localStorage.getItem(THEME_KEY);
            if (saved === 'light' || saved === 'dark') return saved;
            return systemPrefersDark() ? 'dark' : 'light';
        }
        function applyTheme(theme) {
            document.body.classList.toggle('graph-dark', theme === 'dark');
            const btn = document.getElementById('btn-theme');
            btn.textContent = theme === 'dark' ? '☀ Light' : '☾ Dark';
        }
        applyTheme(activeTheme());
        document.getElementById('btn-theme').onclick = () => {
            const next = document.body.classList.contains('graph-dark') ? 'light' : 'dark';
            localStorage.setItem(THEME_KEY, next);
            applyTheme(next);
            if (network) renderGraph();
        };

        function applyPhysics() {
            network.setOptions({
                physics: physicsEnabled ? {
                    barnesHut: { gravitationalConstant: currentGravity, springLength: currentSpring, avoidOverlap: 1 },
                    solver: 'barnesHut',
                    enabled: true
                } : { enabled: false }
            });
        }

        // FULLSCREEN
        document.getElementById('btn-fullscreen').onclick = () => {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
                document.getElementById('btn-fullscreen').innerText = "✖ Exit";
            } else {
                document.exitFullscreen();
                document.getElementById('btn-fullscreen').innerText = "⛶ Fullscreen";
            }
        };

        function filterGraphDataByYear(data) {
            const paperNodes = data.nodes.filter(node => node.group === 'paper');
            const years = [...new Set(paperNodes.map(node => node.publication_date?.slice(0, 4)).filter(year => /^\\d{4}$/.test(year || '')))]
                .sort((a, b) => Number(b) - Number(a));
            const savedYear = localStorage.getItem('uga-selected-year');
            const currentYear = String(new Date().getFullYear());
            const selectedYear = years.includes(savedYear)
                ? savedYear
                : years.includes(currentYear) ? currentYear : years[0];
            const selectedPapers = paperNodes.filter(node => node.publication_date?.startsWith(selectedYear));
            const paperIds = new Set(selectedPapers.map(node => node.id));
            const authoredEdges = data.edges.filter(edge => edge.type === 'authored' && paperIds.has(edge.to));
            const authorsByPaper = new Map();
            authoredEdges.forEach(edge => {
                if (!authorsByPaper.has(edge.to)) authorsByPaper.set(edge.to, []);
                authorsByPaper.get(edge.to).push(edge.from);
            });
            const authorIds = new Set(authoredEdges.map(edge => edge.from));
            const nodes = data.nodes.filter(node =>
                node.group === 'paper' ? paperIds.has(node.id) : node.group === 'author' && authorIds.has(node.id)
            );
            const citedEdges = data.edges.filter(edge =>
                edge.type === 'cited' && paperIds.has(edge.from) && paperIds.has(edge.to)
            );
            const coauthorEdges = [];
            const seenCoauthors = new Set();
            authorsByPaper.forEach(authors => {
                for (let i = 0; i < authors.length; i++) {
                    for (let j = i + 1; j < authors.length; j++) {
                        const pair = [authors[i], authors[j]].sort();
                        const key = JSON.stringify(pair);
                        if (!seenCoauthors.has(key)) {
                            seenCoauthors.add(key);
                            coauthorEdges.push({ from: pair[0], to: pair[1], type: 'coauthor' });
                        }
                    }
                }
            });
            return { nodes, edges: [...citedEdges, ...authoredEdges, ...coauthorEdges] };
        }

        fetch('graph_data.json').then(r => r.json()).then(data => {
            const filteredData = filterGraphDataByYear(data);
            allNodes = filteredData.nodes; allEdges = filteredData.edges;
            allNodes.forEach(n => {
                if (n.cluster_name && !clusterMap[n.cluster_name]) {
                    clusterMap[n.cluster_name] = clusterColors[colorIndex % clusterColors.length];
                    colorIndex++;
                }
            });
            renderGraph();
        });

        function escapeHtml(value) {
            return String(value ?? '').replace(/[&<>"']/g, char => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[char]));
        }

        function safeExternalUrl(value) {
            if (!value) return '';
            try {
                const parsed = new URL(String(value), window.location.origin);
                if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
                    return parsed.href;
                }
            } catch (error) {
                return '';
            }
            return '';
        }

        function formatAuthors(authorsList, ugaAuthorsList) {
            if (!authorsList) return "";
            return authorsList.map(author => ugaAuthorsList && ugaAuthorsList.includes(author.id)
                ? pageAnchor('author', {
                    name: normalizeName(author.name),
                    id: author.id
                }, author.name, 'uga-author-red')
                : escapeHtml(author.name)
            ).join(", ");
        }

        function normalizeName(name) {
            return String(name || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
        }

        function pageLink(pageName, params) {
            const url = new URL(pageName + '/', window.location.href);
            Object.entries(params || {}).forEach(([key, value]) => url.searchParams.set(key, value));
            return url.href;
        }

        function pageAnchor(pageName, params, label, className = '') {
            const safeClass = className ? ` class="${className}"` : '';
            return `<a${safeClass} href="${pageLink(pageName, params)}" target="_top" rel="noopener">${escapeHtml(label)}</a>`;
        }

        function objectPageUrl(node) {
            if (!node) return null;
            if (currentMode === 'cluster' && node.cluster_name) {
                return pageLink('cluster', { name: node.cluster_name });
            }
            if (node.group === 'paper') {
                return pageLink('paper', { id: node.id });
            }
            if (node.group === 'author') {
                const n = node.normalized_name || normalizeName(node.label || '');
                return pageLink('author', { name: n, id: node.id });
            }
            return null;
        }

        function renderGraph(filteredNodeIds = null, selectedNodeId = null) {
            const container = document.getElementById('network');
            let targetGroup = currentMode === 'author' ? 'author' : 'paper';
            let edgeType = targetGroup === 'paper' ? 'cited' : 'coauthor';
            const isFilteredView = !!filteredNodeIds;
            
            let nodesToKeep = allNodes.filter(n => n.group === targetGroup);
            let edgesToKeep = allEdges.filter(e => e.type === edgeType);

            // Cluster Gravity Logic
            if (currentMode === 'cluster') {
                let clusterGroups = {};
                nodesToKeep.forEach(n => {
                    if (!clusterGroups[n.cluster_name]) clusterGroups[n.cluster_name] = [];
                    clusterGroups[n.cluster_name].push(n.id);
                });
                for (let cName in clusterGroups) {
                    let group = clusterGroups[cName];
                    for (let i = 0; i < group.length - 1; i++) {
                        edgesToKeep.push({ from: group[i], to: group[i+1], type: 'gravity', hidden: true, physics: true, length: 35, springConstant: 0.24 });
                    }
                }

                // Spread clusters apart with fixed anchor points around a circle.
                const clusterNames = Object.keys(clusterGroups).filter(Boolean);
                const anchorRadius = Math.max(1200, clusterNames.length * 210);
                clusterNames.forEach((clusterName, idx) => {
                    const angle = (2 * Math.PI * idx) / Math.max(1, clusterNames.length);
                    const anchorId = `cluster-anchor-${idx}`;
                    nodesToKeep.push({
                        id: anchorId,
                        group: 'cluster-anchor',
                        label: '',
                        hidden: true,
                        physics: false,
                        fixed: { x: true, y: true },
                        x: Math.cos(angle) * anchorRadius,
                        y: Math.sin(angle) * anchorRadius,
                    });

                    clusterGroups[clusterName].forEach(nodeId => {
                        edgesToKeep.push({
                            from: nodeId,
                            to: anchorId,
                            type: 'cluster-anchor',
                            hidden: true,
                            physics: true,
                            length: 320,
                            springConstant: 0.02,
                        });
                    });
                });
            } else if (currentMode === 'labs') {
                let labGroups = {};
                nodesToKeep.forEach(n => {
                    const labName = n.uga_lab || (n.uga_authors && n.uga_authors.length ? n.uga_authors.map(id => {
                        const author = allNodes.find(a => a.id === id);
                        return author ? author.label : id;
                    }).join(', ') : 'External / Unaffiliated');
                    n.lab_cluster = labName;
                    if (!labMap[labName]) {
                        labMap[labName] = clusterColors[labColorIndex % clusterColors.length];
                        labColorIndex++;
                    }
                    if (!labGroups[labName]) labGroups[labName] = [];
                    labGroups[labName].push(n.id);
                });
                for (let labName in labGroups) {
                    const group = labGroups[labName];
                    for (let i = 0; i < group.length - 1; i++) {
                        edgesToKeep.push({ from: group[i], to: group[i+1], type: 'gravity', hidden: true, physics: true, length: 15 });
                    }
                }
            }

            if (filteredNodeIds) {
                nodesToKeep = nodesToKeep.filter(n => filteredNodeIds.has(n.id));
                edgesToKeep = edgesToKeep.filter(e => filteredNodeIds.has(e.from) && filteredNodeIds.has(e.to) && e.type !== 'gravity');
                document.getElementById('btn-reset').style.display = 'block';
            } else {
                document.getElementById('btn-reset').style.display = 'none';
            }

            // NEW: Sub-graph Paper Injection in Author Mode
            if (currentMode === 'author' && selectedNodeId) {
                let authoredEdges = allEdges.filter(e => e.type === 'authored');
                // Get all papers this selected author contributed to
                let selectedPapers = authoredEdges.filter(e => e.from === selectedNodeId).map(e => e.to);
                
                let paperNodes = allNodes.filter(n => n.group === 'paper' && selectedPapers.includes(n.id));
                nodesToKeep = nodesToKeep.concat(paperNodes); // Inject Papers
                
                // Add edges from ALL rendered authors to those papers
                let renderedNodes = new Set(nodesToKeep.map(n => n.id));
                let subEdges = authoredEdges.filter(e => renderedNodes.has(e.from) && renderedNodes.has(e.to));
                edgesToKeep = edgesToKeep.concat(subEdges);
            }

            const hideLabels = nodesToKeep.length > 10;

            let finalNodes = nodesToKeep.map(n => {
                let nodeData = { ...n };
                
                // Tooltips
                if (nodeData.group === 'paper') {
                    let authHtml = formatAuthors(nodeData.authors_raw, nodeData.uga_authors);
                    let labHtml = nodeData.uga_lab ? `<br><span style="color:#ff0000;">Lab:</span> ${escapeHtml(nodeData.uga_lab)}` : '';
                    let venue = nodeData.venue && nodeData.venue !== 'Unknown'
                        ? pageAnchor('venue', { name: nodeData.venue }, nodeData.venue)
                        : escapeHtml(nodeData.venue || 'Unknown');
                    let cluster = nodeData.cluster_name
                        ? pageAnchor('cluster', { name: nodeData.cluster_name }, nodeData.cluster_name)
                        : 'Unassigned';
                    nodeData.hoverHtml = `
                        <div style="font-size: 14px; margin-bottom: 6px;"><b>${escapeHtml(nodeData.label)}</b></div>
                        <div style="font-size: 12px; color:#ccc; line-height:1.55;">
                            Published: ${escapeHtml(nodeData.publication_date || 'Unknown')}<br>
                            Conference: ${venue}<br>
                            Cluster: ${cluster}<br>
                            Authors: ${authHtml} ${labHtml}
                        </div>`;
                } else if (nodeData.group === 'author') {
                    let affil = nodeData.is_uga ? "<span class='uga-author-red'>UGA Affiliate</span>" : "<span style='color:#888;'>External</span>";
                    let authorName = nodeData.is_uga
                        ? pageAnchor('author', { name: nodeData.normalized_name || normalizeName(nodeData.label), id: nodeData.id }, nodeData.label, 'uga-author-red')
                        : escapeHtml(nodeData.label);
                    nodeData.hoverHtml = `<div style="font-size: 14px;"><b>${authorName}</b></div><div style="font-size:12px; margin-top:4px;">${affil}</div>`;
                }

                // Styling Overrides
                if (currentMode === 'paper') {
                    nodeData.color = { background: '#ff0000', border: '#aa0000' };
                    const labelColor = document.body.classList.contains('graph-dark') ? '#ffffff' : '#000000';
                    const labelBackground = document.body.classList.contains('graph-dark') ? '#1f2430' : '#ffffff';
                    nodeData.font = { color: labelColor, background: labelBackground, strokeWidth: 2, strokeColor: labelBackground };
                } else if (currentMode === 'cluster' && nodeData.cluster_name) {
                    nodeData.color = { background: clusterMap[nodeData.cluster_name], border: '#ffffff' };
                    const labelColor = document.body.classList.contains('graph-dark') ? '#ffffff' : '#000000';
                    const labelBackground = document.body.classList.contains('graph-dark') ? '#1f2430' : '#ffffff';
                    nodeData.font = { color: labelColor, background: labelBackground, strokeWidth: 2, strokeColor: labelBackground };
                } else if (currentMode === 'labs' && nodeData.lab_cluster) {
                    nodeData.color = { background: labMap[nodeData.lab_cluster], border: '#ffffff' };
                    const labelColor = document.body.classList.contains('graph-dark') ? '#ffffff' : '#000000';
                    const labelBackground = document.body.classList.contains('graph-dark') ? '#1f2430' : '#ffffff';
                    nodeData.font = { color: labelColor, background: labelBackground, strokeWidth: 2, strokeColor: labelBackground };
                } else if (currentMode === 'author') {
                    if (nodeData.group === 'paper') {
                        nodeData.color = { background: '#ff0000', border: '#aa0000' };
                        const labelColor = document.body.classList.contains('graph-dark') ? '#ffffff' : '#000000';
                        const labelBackground = document.body.classList.contains('graph-dark') ? '#1f2430' : '#ffffff';
                        nodeData.font = { color: labelColor, background: labelBackground, strokeWidth: 2, strokeColor: labelBackground };
                        nodeData.shape = 'box';
                    } else {
                        if (nodeData.is_uga) nodeData.color = { background: '#ff0000', border: '#aa0000' };
                        else nodeData.color = { background: '#555555', border: '#333333' };
                        const labelColor = document.body.classList.contains('graph-dark') ? '#ffffff' : '#000000';
                        const labelBackground = document.body.classList.contains('graph-dark') ? '#1f2430' : '#ffffff';
                        nodeData.font = { color: labelColor, background: labelBackground, strokeWidth: 2, strokeColor: labelBackground };
                    }
                }

                if (selectedNodeId && n.id === selectedNodeId) {
                    nodeData.color = { background: '#ffffff', border: '#ff0000' };
                    nodeData.font = { color: '#000000', background: 'white' };
                }
                if (hideLabels) {
                    nodeData.label = '';
                }
                return nodeData;
            });

            // Styling edges to be semi-transparent when injecting papers
            let finalEdges = edgesToKeep.map(e => {
                let edgeData = { ...e };
                if (e.type === 'authored') {
                    edgeData.color = { color: 'rgba(255, 0, 0, 0.3)' };
                    edgeData.dashes = true;
                } else if (currentMode === 'cluster' && e.type === 'cited') {
                    edgeData.physics = false;
                } else if (!document.body.classList.contains('graph-dark')) {
                    edgeData.color = { color: '#111111', opacity: 1 };
                }
                return edgeData;
            });

            const finalNodeMap = new Map(finalNodes.map(node => [node.id, node]));

            const isAuthorMode = currentMode === 'author';
            const baseSpringLength = currentMode === 'cluster' ? Math.max(currentSpring * 2.2, 320) : currentSpring;
            const baseGravity = currentMode === 'cluster' ? currentGravity * 3.5 : currentGravity * 2;
            const stabilizationIterations = isAuthorMode ? 120 : 300;

            const data = { nodes: new vis.DataSet(finalNodes), edges: new vis.DataSet(finalEdges) };
            const options = {
                nodes: { shape: 'dot', font: { size: 14, face: 'monospace' }, shadow: !isAuthorMode },
                edges: {
                    width: isAuthorMode ? 1 : 1.5,
                    color: { inherit: 'both' },
                    smooth: isAuthorMode ? false : { type: 'continuous' }
                },
                interaction: { hover: true, dragNodes: true, dragView: true, zoomView: true },
                physics: {
                    enabled: true,
                    barnesHut: {
                        gravitationalConstant: baseGravity,
                        springLength: baseSpringLength,
                        avoidOverlap: 2
                    },
                    solver: 'barnesHut',
                    stabilization: { iterations: stabilizationIterations, fit: true }
                }
            };

            if (network) network.destroy();
            network = new vis.Network(container, data, options);
            hideTooltip();

            if (!physicsEnabled) {
                network.once('stabilizationIterationsDone', function() {
                    network.setOptions({ physics: { enabled: false } });
                    network.fit({ animation: false });
                });
            } else {
                applyPhysics();
            }

            network.once('stabilizationIterationsDone', function() {
                if (!hasInitialFit) {
                    network.fit({ animation: false });
                    hasInitialFit = true;
                }
            });

            network.on("hoverNode", function (params) {
                const node = finalNodeMap.get(params.node);
                if (node && node.hoverHtml) {
                    tooltip.innerHTML = node.hoverHtml;
                    tooltip.style.display = 'block';
                    tooltip.style.left = tooltipAnchor.x + 'px';
                    tooltip.style.top = tooltipAnchor.y + 'px';
                }
            });
            network.on("blurNode", function () {
                scheduleTooltipHide();
            });
            network.on("deselectNode", hideTooltip);
            network.on("dragStart", hideTooltip);
            network.on("zoom", hideTooltip);
            network.on("click", function(params) {
                if (!params.nodes || params.nodes.length === 0) hideTooltip();
            });
            container.onmouseleave = scheduleTooltipHide;

            network.on("beforeDrawing", function(ctx) {
                if (currentMode !== 'cluster' && currentMode !== 'labs') return;
                
                let regionPositions = {};
                for (let nodeId in network.body.nodes) {
                    let node = network.body.nodes[nodeId];
                    const regionName = currentMode === 'cluster' ? node.options.cluster_name : node.options.lab_cluster;
                    if (regionName) {
                        if (!regionPositions[regionName]) regionPositions[regionName] = [];
                        regionPositions[regionName].push(node);
                    }
                }

                for (let regionName in regionPositions) {
                    let nodes = regionPositions[regionName];
                    if (nodes.length === 0) continue;
                    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                    nodes.forEach(n => {
                        minX = Math.min(minX, n.x); minY = Math.min(minY, n.y);
                        maxX = Math.max(maxX, n.x); maxY = Math.max(maxY, n.y);
                    });
                    let centerX = (minX + maxX) / 2;
                    let centerY = (minY + maxY) / 2;
                    let radius = Math.max(maxX - minX, maxY - minY) / 2 + 100;
                    const regionColor = currentMode === 'cluster' ? clusterMap[regionName] : labMap[regionName];

                    ctx.fillStyle = regionColor + '22';
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                    ctx.fill();

                    ctx.fillStyle = document.body.classList.contains('graph-dark') ? '#ffffff' : '#000000';
                    ctx.font = "bold 20px monospace";
                    ctx.textAlign = "center";
                    ctx.fillText(regionName, centerX, minY - 60);
                }
            });

            network.on("selectNode", function (params) {
                const nodeId = params.nodes[0];
                const selectedNode = allNodes.find(n => n.id === nodeId);
                const destination = objectPageUrl(selectedNode);

                if (!isFilteredView && destination) {
                    window.top.location.href = destination;
                    return;
                }
                
                const relatedNodeIds = new Set([nodeId]);
                allEdges.forEach(e => {
                    if (e.type === edgeType) {
                        if (e.from === nodeId) relatedNodeIds.add(e.to);
                        if (e.to === nodeId) relatedNodeIds.add(e.from);
                    }
                });

                const header = document.getElementById('header-info');
                if (targetGroup === 'paper' || (currentMode === 'author' && selectedNode.group === 'paper')) {
                    let auths = formatAuthors(selectedNode.authors_raw, selectedNode.uga_authors);
                    let lab = selectedNode.uga_lab ? ` | <span style="color:#ff0000">${escapeHtml(selectedNode.uga_lab)}</span>` : '';
                    let safeUrl = safeExternalUrl(selectedNode.url);
                    let link = safeUrl ? `<a href="${safeUrl}" target="_blank" rel="noopener">[View]</a>` : '';
                    let venue = selectedNode.venue && selectedNode.venue !== 'Unknown'
                        ? pageAnchor('venue', { name: selectedNode.venue }, selectedNode.venue)
                        : escapeHtml(selectedNode.venue || 'Unknown');
                    let cluster = selectedNode.cluster_name
                        ? pageAnchor('cluster', { name: selectedNode.cluster_name }, selectedNode.cluster_name)
                        : 'Unassigned';
                    header.innerHTML = `<div style="margin-bottom: 2px;"><b>${escapeHtml(selectedNode.label)}</b> ${link}</div><div style="font-size:12px;color:#aaa;">Published: ${escapeHtml(selectedNode.publication_date || 'Unknown')} · Conference: ${venue} · Cluster: ${cluster}${lab}<br>By: ${auths}</div>`;
                } else {
                    let affil = selectedNode.is_uga ? "(UGA IAI Faculty/Student)" : "(External Collaborator)";
                    let authorName = selectedNode.is_uga
                        ? pageAnchor('author', { name: selectedNode.normalized_name || normalizeName(selectedNode.label), id: selectedNode.id }, selectedNode.label, 'uga-author-red')
                        : escapeHtml(selectedNode.label);
                    header.innerHTML = `<div><b>${authorName}</b> ${affil}</div>`;
                }

                // If user clicks an injected paper in author mode, switch to paper mode to view it properly
                if (currentMode === 'author' && selectedNode.group === 'paper') {
                    currentMode = 'paper';
                    renderGraph(null, nodeId);
                    network.selectNodes([nodeId]);
                } else {
                    renderGraph(relatedNodeIds, nodeId);
                }
            });
        }

        // CTRL+F Logic omitted for brevity (Keep identical to previous block)
        document.addEventListener("keydown", function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === "f") {
                e.preventDefault();
                document.getElementById("search-modal").style.display = "block";
                document.getElementById("search-input").focus();
            }
            if (e.key === "Escape") {
                document.getElementById("search-modal").style.display = "none";
                document.getElementById("settings-panel").style.display = "none";
            }
        });

        document.getElementById("search-input").addEventListener("keyup", function(e) {
            let q = e.target.value.toLowerCase();
            let resultsDiv = document.getElementById("search-results");
            resultsDiv.innerHTML = "";
            if (!q) return;

            let matches = allNodes.filter(n => {
                if (n.group !== 'paper') return false;
                let titleMatch = n.label.toLowerCase().includes(q);
                let labMatch = n.uga_lab && n.uga_lab.toLowerCase().includes(q);
                let authMatch = n.authors_raw && n.authors_raw.some(a => a.name.toLowerCase().includes(q));
                return titleMatch || labMatch || authMatch;
            }).slice(0, 10);

            matches.forEach(m => {
                let div = document.createElement("div");
                div.className = "search-item";
                div.innerHTML = `<b>${escapeHtml(m.label)}</b><br><span style="font-size:11px; color:#aaa">${escapeHtml(m.uga_lab || "Unknown Lab")}</span>`;
                div.onclick = () => {
                    currentMode = 'paper';
                    renderGraph(null, null);
                    network.selectNodes([m.id]);
                    network.focus(m.id, {scale: 1.2, animation: {duration: 500}});
                    document.getElementById("search-modal").style.display = "none";
                    network.emit("selectNode", {nodes: [m.id]});
                };
                resultsDiv.appendChild(div);
            });
        });

        document.getElementById('btn-paper').onclick = () => { currentMode = 'paper'; renderGraph(); };
        document.getElementById('btn-cluster').onclick = () => { currentMode = 'cluster'; renderGraph(); };
        document.getElementById('btn-labs').onclick = () => { currentMode = 'labs'; renderGraph(); };
        document.getElementById('btn-author').onclick = () => { currentMode = 'author'; renderGraph(); };
        document.getElementById('btn-reset').onclick = () => { renderGraph(); document.getElementById('header-info').innerHTML = "<i>Select a node or use Ctrl+F to search the IAI database...</i>"; };

        window.addEventListener('resize', () => {
            if (network) {
                network.setSize('100%', '100%');
                network.fit({ animation: false });
            }
        });
    </script>
</body>
</html>
"""


def build_interactive_graph():
    if not os.path.exists("data/papers_raw.json"):
        return

    with open("data/papers_raw.json", "r") as f:
        papers = json.load(f)
    if not isinstance(papers, list):
        papers = []

    roster_by_name = {}
    roster_path = "data/iai_roster.json"
    if os.path.exists(roster_path):
        with open(roster_path, "r") as f:
            roster = json.load(f)
        if not isinstance(roster, list):
            roster = []
        roster_by_name = {
            person.get("normalized_name"): person
            for person in roster
            if isinstance(person, dict) and person.get("normalized_name")
        }
        known_uga_labs = {
            lab
            for person in roster
            if isinstance(person, dict)
            for lab in person.get("labs", [])
            if lab and lab != "Uncertain"
        }
    else:
        known_uga_labs = set()

    nodes = []
    edges = []
    author_nodes = {}
    coauthors = set()

    for p in papers:
        if not isinstance(p, dict):
            continue

        paper_id = safe_identifier(p.get("id"))
        if not paper_id:
            continue

        paper_title = safe_text(p.get("title"), max_len=3000) or "Untitled"
        paper_cluster = safe_text(p.get("cluster_name"), max_len=128) or None
        paper_url = safe_url(p.get("url"))
        paper_venue = safe_text(p.get("venue"), max_len=400) or "Unknown"
        paper_publication_date = safe_date(p.get("publication_date"))
        paper_abstract = sanitize_abstract(p.get("abstract", {}))
        paper_refs = sanitize_reference_list(p.get("referenced_works", []))
        paper_authors = sanitize_author_list(p.get("authors", []))

        uga_authors_raw = p.get("uga_authors", [])
        if isinstance(uga_authors_raw, list):
            uga_authors = [aid for aid in (
                safe_identifier(x) for x in uga_authors_raw) if aid]
        else:
            uga_authors = []
        uga_authors = sorted(set(uga_authors), key=str)

        uga_labs_raw = p.get("uga_labs", [])
        if isinstance(uga_labs_raw, list):
            uga_labs = [safe_text(lab, max_len=200) for lab in uga_labs_raw]
            uga_labs = sorted(
                {lab for lab in uga_labs if lab in known_uga_labs})
        else:
            uga_labs = []

        uga_lab = ", ".join(uga_labs) or None

        nodes.append(
            {
                "id": paper_id,
                "label": paper_title,
                "group": "paper",
                "size": 16,
                "cluster_name": paper_cluster,
                "url": paper_url,
                "uga_lab": uga_lab,
                "uga_labs": uga_labs,
                "uga_authors": uga_authors,
                "authors_raw": paper_authors,
                "abstract": paper_abstract,
                "venue": paper_venue,
                "publication_date": paper_publication_date,
            }
        )

        for ref in paper_refs:
            edges.append({"from": paper_id, "to": ref, "type": "cited"})

        auths = paper_authors
        valid_auths = []
        uga_auth_ids = uga_authors
        for a in auths:
            author_id = a.get("id")
            if not author_id:
                continue

            author_name = a.get("name") or "Unknown author"
            valid_auths.append({"id": author_id, "name": author_name})

            # NEW: Log authored edges so we can display papers in Author mode
            edges.append(
                {"from": author_id, "to": paper_id, "type": "authored"})
            if author_id not in author_nodes:
                normalized = normalize_name(author_name)
                roster_person = roster_by_name.get(normalized)
                author_nodes[author_id] = {
                    "id": author_id,
                    "label": author_name,
                    "normalized_name": normalized,
                    "group": "author",
                    "size": 12,
                    "is_uga": author_id in uga_auth_ids,
                    "roster_status": roster_person.get("status") if roster_person else None,
                    "roster_title": roster_person.get("title") if roster_person else None,
                    "roster_profile_url": roster_person.get("profile_url")
                    if roster_person
                    else None,
                    "roster_email": roster_person.get("email") if roster_person else None,
                }
            if author_id in uga_auth_ids:
                author_nodes[author_id]["is_uga"] = True

        for i in range(len(valid_auths)):
            for j in range(i + 1, len(valid_auths)):
                pair = tuple(
                    sorted([valid_auths[i]["id"], valid_auths[j]["id"]]))
                if pair not in coauthors:
                    coauthors.add(pair)
                    edges.append(
                        {"from": pair[0], "to": pair[1], "type": "coauthor"})

    nodes.extend(list(author_nodes.values()))
    os.makedirs("docs", exist_ok=True)
    with open("docs/graph_data.json", "w") as f:
        json.dump({"nodes": nodes, "edges": edges}, f)
    with open("docs/graph_app.html", "w") as f:
        f.write(HTML_TEMPLATE)
    print(
        "Graph app updated for minimal UI, bipartite author injections, and dynamic node collision."
    )


if __name__ == "__main__":
    build_interactive_graph()
