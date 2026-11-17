import json
import os

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>IAI Research Explorer</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
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
        
        #header-controls { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
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
            color: var(--g-tooltip-text); z-index: 100; pointer-events: none; max-width: 320px; line-height: 1.4;
        }

        #search-modal { display: none; position: absolute; top: 70px; left: 20px; background: var(--g-panel-bg); color: var(--g-panel-text); padding: 15px; border: 1px solid var(--g-btn-primary); z-index: 30; width: 300px; }
        #search-modal input { width: 100%; padding: 8px; box-sizing: border-box; margin-bottom: 10px; background: var(--g-bg); border: 1px solid var(--g-border); color: var(--g-text); }
        #search-results { max-height: 200px; overflow-y: auto; font-size: 13px; }
        .search-item { padding: 8px; border-bottom: 1px solid #333; cursor: pointer; }
        .search-item:hover { background: #ff0000; color: #000; }
        .search-hint { position: absolute; bottom: 20px; left: 20px; background: var(--g-hint-bg); border: 1px solid var(--g-border); color: var(--g-hint-text); padding: 5px 10px; font-size: 12px; z-index: 10; pointer-events: none;}
    </style>
</head>
<body>
    <div id="header-bar">
        <div id="header-info"><i>Select a node or use Ctrl+F to search the IAI database...</i></div>
        
        <div id="header-controls">
            <button id="btn-paper">Paper Citations</button>
            <button id="btn-cluster">Cluster Regions</button>
            <button id="btn-cluster-rep" class="secondary">Repulsion: Medium</button>
            <button id="btn-author">Co-Authorships</button>
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
            <label>Node Gravity (<span id="val-gravity"></span>)</label>
            <input type="range" id="inp-gravity" min="-8000" max="-500" step="100">
        </div>
        <div class="setting-row">
            <label>Cluster Repulsion Weight (<span id="val-cluster"></span>)</label>
            <input type="range" id="inp-cluster" min="-15000" max="-2000" step="500">
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

    <script>
        let allNodes = []; let allEdges = [];
        let network = null; let currentMode = 'paper';
        let hasInitialFit = false;
        const clusterColors = ["#ff0000", "#1a73e8", "#fbbc04", "#34a853", "#8e24aa", "#ff6d00"];
        let clusterMap = {}; let colorIndex = 0;

        // PHYSICS PARAMS
        let currentGravity = -3000;
        let currentSpring = 150;
        let currentClusterRep = -8000; // New independent repulsion weight for clusters
        const clusterRepPresets = [
            { label: 'Mild', value: -5000 },
            { label: 'Medium', value: -8000 },
            { label: 'Strong', value: -12000 }
        ];
        let clusterRepIndex = 1;
        
        if (localStorage.getItem('iai_graph_gravity')) currentGravity = parseInt(localStorage.getItem('iai_graph_gravity'));
        if (localStorage.getItem('iai_graph_spring')) currentSpring = parseInt(localStorage.getItem('iai_graph_spring'));
        if (localStorage.getItem('iai_graph_cluster')) currentClusterRep = parseInt(localStorage.getItem('iai_graph_cluster'));
        
        document.getElementById('inp-gravity').value = currentGravity;
        document.getElementById('inp-spring').value = currentSpring;
        document.getElementById('inp-cluster').value = currentClusterRep;
        
        document.getElementById('val-gravity').innerText = currentGravity;
        document.getElementById('val-spring').innerText = currentSpring;
        document.getElementById('val-cluster').innerText = currentClusterRep;

        const presetMatch = clusterRepPresets.findIndex((p) => p.value === currentClusterRep);
        if (presetMatch >= 0) clusterRepIndex = presetMatch;
        document.getElementById('btn-cluster-rep').innerText = `Repulsion: ${clusterRepPresets[clusterRepIndex].label}`;

        document.getElementById('inp-gravity').oninput = (e) => { currentGravity = parseInt(e.target.value); document.getElementById('val-gravity').innerText = currentGravity; if(network) applyPhysics(); };
        document.getElementById('inp-spring').oninput = (e) => { currentSpring = parseInt(e.target.value); document.getElementById('val-spring').innerText = currentSpring; if(network) applyPhysics(); };
        document.getElementById('inp-cluster').oninput = (e) => { currentClusterRep = parseInt(e.target.value); document.getElementById('val-cluster').innerText = currentClusterRep; if(network) applyPhysics(); };

        document.getElementById('btn-cluster-rep').onclick = () => {
            clusterRepIndex = (clusterRepIndex + 1) % clusterRepPresets.length;
            currentClusterRep = clusterRepPresets[clusterRepIndex].value;
            document.getElementById('inp-cluster').value = currentClusterRep;
            document.getElementById('val-cluster').innerText = currentClusterRep;
            document.getElementById('btn-cluster-rep').innerText = `Repulsion: ${clusterRepPresets[clusterRepIndex].label}`;
            if (network) applyPhysics();
        };

        document.getElementById('btn-settings').onclick = () => {
            const p = document.getElementById('settings-panel');
            p.style.display = p.style.display === 'block' ? 'none' : 'block';
        };
        document.getElementById('btn-save-settings').onclick = () => {
            localStorage.setItem('iai_graph_gravity', currentGravity);
            localStorage.setItem('iai_graph_spring', currentSpring);
            localStorage.setItem('iai_graph_cluster', currentClusterRep);
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
            // avoidOverlap: 1 pushes nodes physically apart so labels are readable
            let activeGravity = currentMode === 'cluster' ? currentClusterRep : currentGravity;
            network.setOptions({
                physics: { 
                    barnesHut: { gravitationalConstant: activeGravity, springLength: currentSpring, avoidOverlap: 1 },
                    solver: 'barnesHut'
                }
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

        fetch('graph_data.json').then(r => r.json()).then(data => {
            allNodes = data.nodes; allEdges = data.edges;
            allNodes.forEach(n => {
                if (n.cluster_name && !clusterMap[n.cluster_name]) {
                    clusterMap[n.cluster_name] = clusterColors[colorIndex % clusterColors.length];
                    colorIndex++;
                }
            });
            renderGraph();
        });

        function formatAuthors(authorsList, ugaAuthorsList) {
            if (!authorsList) return "";
            return authorsList.map(a => 
                ugaAuthorsList && ugaAuthorsList.includes(a.id) 
                ? `<span class="uga-author-red">${a.name}</span>` 
                : a.name
            ).join(", ");
        }

        function renderGraph(filteredNodeIds = null, selectedNodeId = null) {
            const container = document.getElementById('network');
            let targetGroup = currentMode === 'author' ? 'author' : 'paper';
            let edgeType = targetGroup === 'paper' ? 'cited' : 'coauthor';
            
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

            let finalNodes = nodesToKeep.map(n => {
                let nodeData = { ...n };
                
                // Tooltips
                if (nodeData.group === 'paper') {
                    let authHtml = formatAuthors(nodeData.authors_raw, nodeData.uga_authors);
                    let labHtml = nodeData.uga_lab ? `<br><span style="color:#ff0000;">Lab:</span> ${nodeData.uga_lab}` : '';
                    nodeData.hoverHtml = `
                        <div style="font-size: 14px; margin-bottom: 6px;"><b>${nodeData.label}</b></div>
                        <div style="font-size: 12px; color:#ccc;">
                            Authors: ${authHtml} ${labHtml}
                        </div>`;
                } else if (nodeData.group === 'author') {
                    let affil = nodeData.is_uga ? "<span class='uga-author-red'>UGA Affiliate</span>" : "<span style='color:#888;'>External</span>";
                    nodeData.hoverHtml = `<div style="font-size: 14px;"><b>${nodeData.label}</b></div><div style="font-size:12px; margin-top:4px;">${affil}</div>`;
                }

                // Styling Overrides
                if (currentMode === 'paper') {
                    nodeData.color = { background: '#ff0000', border: '#aa0000' };
                    nodeData.font = { color: '#ffffff' };
                } else if (currentMode === 'cluster' && nodeData.cluster_name) {
                    nodeData.color = { background: clusterMap[nodeData.cluster_name], border: '#ffffff' };
                    nodeData.font = { color: '#ffffff' };
                } else if (currentMode === 'author') {
                    if (nodeData.group === 'paper') {
                        // Semi-transparent styling for injected papers
                        nodeData.color = { background: 'rgba(255, 0, 0, 0.2)', border: 'rgba(255, 0, 0, 0.4)' };
                        nodeData.font = { color: 'rgba(255,255,255,0.6)' };
                        nodeData.shape = 'box';
                    } else {
                        // Standard Author Styling
                        if (nodeData.is_uga) nodeData.color = { background: '#ff0000', border: '#aa0000' };
                        else nodeData.color = { background: '#555555', border: '#333333' };
                        nodeData.font = { color: '#ffffff' };
                    }
                }

                if (selectedNodeId && n.id === selectedNodeId) {
                    nodeData.color = { background: '#ffffff', border: '#ff0000' };
                    nodeData.font = { color: '#000000', background: 'white' };
                }
                return nodeData;
            });

            // Styling edges to be semi-transparent when injecting papers
            let finalEdges = edgesToKeep.map(e => {
                let edgeData = { ...e };
                if (e.type === 'authored') {
                    edgeData.color = { color: 'rgba(255, 0, 0, 0.3)' };
                    edgeData.dashes = true;
                }
                return edgeData;
            });

            const data = { nodes: new vis.DataSet(finalNodes), edges: new vis.DataSet(finalEdges) };
            const options = {
                nodes: { shape: 'dot', font: { size: 14, face: 'monospace' }, shadow: true },
                edges: { width: 1.5, color: { inherit: 'both' }, smooth: { type: 'continuous' } },
                interaction: { hover: true }
            };

            if (network) network.destroy();
            network = new vis.Network(container, data, options);
            applyPhysics();

            network.once('stabilizationIterationsDone', function() {
                if (!hasInitialFit) {
                    network.fit({ animation: false });
                    hasInitialFit = true;
                }
            });

            network.on("hoverNode", function (params) {
                const node = finalNodes.find(n => n.id === params.node);
                if (node && node.hoverHtml) {
                    const tooltip = document.getElementById('custom-tooltip');
                    tooltip.innerHTML = node.hoverHtml;
                    tooltip.style.display = 'block';
                }
            });
            network.on("blurNode", function () {
                document.getElementById('custom-tooltip').style.display = 'none';
            });
            document.addEventListener('mousemove', function(e) {
                const tooltip = document.getElementById('custom-tooltip');
                if (tooltip.style.display === 'block') {
                    tooltip.style.left = (e.pageX + 15) + 'px';
                    tooltip.style.top = (e.pageY + 15) + 'px';
                }
            });

            network.on("beforeDrawing", function(ctx) {
                if (currentMode !== 'cluster') return;
                
                let clusterPositions = {};
                for (let nodeId in network.body.nodes) {
                    let node = network.body.nodes[nodeId];
                    if (node.options.cluster_name) {
                        if (!clusterPositions[node.options.cluster_name]) clusterPositions[node.options.cluster_name] = [];
                        clusterPositions[node.options.cluster_name].push(node);
                    }
                }

                for (let cName in clusterPositions) {
                    let nodes = clusterPositions[cName];
                    if (nodes.length === 0) continue;
                    
                    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                    nodes.forEach(n => {
                        minX = Math.min(minX, n.x); minY = Math.min(minY, n.y);
                        maxX = Math.max(maxX, n.x); maxY = Math.max(maxY, n.y);
                    });
                    
                    let centerX = (minX + maxX) / 2;
                    let centerY = (minY + maxY) / 2;
                    let radius = Math.max(maxX - minX, maxY - minY) / 2 + 100;

                    ctx.fillStyle = clusterMap[cName] + '22';
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                    ctx.fill();

                    ctx.fillStyle = "rgba(255,255,255,0.7)";
                    ctx.font = "bold 20px monospace";
                    ctx.textAlign = "center";
                    ctx.fillText(cName, centerX, minY - 60);
                }
            });

            network.on("selectNode", function (params) {
                const nodeId = params.nodes[0];
                const selectedNode = allNodes.find(n => n.id === nodeId);
                
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
                    let lab = selectedNode.uga_lab ? ` | <span style="color:#ff0000">${selectedNode.uga_lab}</span>` : '';
                    let link = selectedNode.url ? `<a href="${selectedNode.url}" target="_blank">[View]</a>` : '';
                    header.innerHTML = `<div style="margin-bottom: 2px;"><b>${selectedNode.label}</b> ${lab} ${link}</div> <div style="font-size:12px; color:#aaa;">By: ${auths}</div>`;
                } else {
                    let affil = selectedNode.is_uga ? "(UGA IAI Faculty/Student)" : "(External Collaborator)";
                    header.innerHTML = `<div><b style="color:#ff0000">${selectedNode.label}</b> ${affil}</div>`;
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
                div.innerHTML = `<b>${m.label}</b><br><span style="font-size:11px; color:#aaa">${m.uga_lab || "Unknown Lab"}</span>`;
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
        document.getElementById('btn-author').onclick = () => { currentMode = 'author'; renderGraph(); };
        document.getElementById('btn-reset').onclick = () => { renderGraph(); document.getElementById('header-info').innerHTML = "<i>Select a node or use Ctrl+F to search the IAI database...</i>"; };
    </script>
</body>
</html>
"""

def build_interactive_graph():
    if not os.path.exists("data/papers_raw.json"):
        return

    with open("data/papers_raw.json", "r") as f:
        papers = json.load(f)

    nodes = []
    edges = []
    author_nodes = {}
    coauthors = set()

    for p in papers:
        nodes.append({
            "id": p["id"], "label": p["title"], "group": "paper", "size": 16,
            "cluster_name": p.get("cluster_name"),
            "url": p.get("url"),
            "uga_lab": p.get("uga_lab"),
            "uga_authors": p.get("uga_authors", []),
            "authors_raw": p.get("authors", [])
        })
        
        for ref in p.get("referenced_works", []):
            edges.append({"from": p["id"], "to": ref, "type": "cited"})

        auths = p.get("authors", [])
        uga_auth_ids = p.get("uga_authors", [])
        
        for a in auths:
            # NEW: Log authored edges so we can display papers in Author mode
            edges.append({"from": a["id"], "to": p["id"], "type": "authored"})
            
            if a["id"] not in author_nodes:
                author_nodes[a["id"]] = {
                    "id": a["id"], "label": a["name"], "group": "author", "size": 12,
                    "is_uga": a["id"] in uga_auth_ids
                }
            if a["id"] in uga_auth_ids:
                author_nodes[a["id"]]["is_uga"] = True
        
        for i in range(len(auths)):
            for j in range(i+1, len(auths)):
                pair = tuple(sorted([auths[i]["id"], auths[j]["id"]]))
                if pair not in coauthors:
                    coauthors.add(pair)
                    edges.append({"from": pair[0], "to": pair[1], "type": "coauthor"})

    nodes.extend(list(author_nodes.values()))

    os.makedirs("docs", exist_ok=True)
    with open("docs/graph_data.json", "w") as f:
        json.dump({"nodes": nodes, "edges": edges}, f)
    with open("docs/graph_app.html", "w") as f:
        f.write(HTML_TEMPLATE)
    print("Graph app updated for minimal UI, bipartite author injections, and dynamic node collision.")

if __name__ == "__main__":
    build_interactive_graph()