(() => {
    const canvas = document.getElementById('gpu-network');
    const visNetwork = document.getElementById('network');
    if (!canvas) return;
    if (visNetwork) visNetwork.style.display = 'none';
    canvas.style.cssText = 'position:absolute;inset:60px 0 0 0;width:100%;height:calc(100% - 60px);display:block;touch-action:none;';

    let data = null;
    let nodes = [];
    let selected = null;
    let hovered = null;
    let view = { x: 0, y: 0, scale: 1 };
    let dragging = false;
    let dragStart = null;

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[c]));
    }

    async function init() {
        const response = await fetch('graph_data.json');
        data = await response.json();
        const selectedYear = localStorage.getItem('uga-selected-year') || String(new Date().getFullYear());
        const paperNodes = data.nodes.filter(n => n.group === 'paper' && typeof n.publication_date === 'string' && n.publication_date.startsWith(selectedYear));
        nodes = paperNodes.map((n, i) => {
            const angle = i * 2.399963229728653;
            const radius = 25 * Math.sqrt(i + 1);
            return { ...n, x: Math.cos(angle) * radius, y: Math.sin(angle) * radius, vx: 0, vy: 0, paper: true };
        });
        fit();
        requestAnimationFrame(render);
    }

    function fit() {
        if (!nodes.length) return;
        const rect = canvas.getBoundingClientRect();
        const xs = nodes.map(n => n.x), ys = nodes.map(n => n.y);
        const spanX = Math.max(1, Math.max(...xs) - Math.min(...xs));
        const spanY = Math.max(1, Math.max(...ys) - Math.min(...ys));
        view.scale = Math.min(rect.width / (spanX + 160), rect.height / (spanY + 160));
        view.x = rect.width / 2;
        view.y = rect.height / 2;
    }

    function screenPoint(n) {
        return { x: view.x + n.x * view.scale, y: view.y + n.y * view.scale };
    }

    function draw2d(ctx, rect) {
        ctx.clearRect(0, 0, rect.width, rect.height);
        ctx.fillStyle = getComputedStyle(document.body).backgroundColor || '#fff';
        ctx.fillRect(0, 0, rect.width, rect.height);

        ctx.strokeStyle = document.body.classList.contains('graph-dark') ? 'rgba(180,190,210,.16)' : 'rgba(40,40,40,.12)';
        ctx.lineWidth = 1;
        data.edges.forEach(edge => {
            if (edge.type !== 'cited') return;
            const a = nodes.find(n => n.id === edge.from);
            const b = nodes.find(n => n.id === edge.to);
            if (!a || !b) return;
            const pa = screenPoint(a), pb = screenPoint(b);
            ctx.beginPath(); ctx.moveTo(pa.x, pa.y); ctx.lineTo(pb.x, pb.y); ctx.stroke();
        });

        nodes.forEach(n => {
            const p = screenPoint(n);
            const r = n.id === selected ? 7 : n.id === hovered ? 6 : 4;
            ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
            ctx.fillStyle = (n.uga_authors || []).length ? '#e0002f' : '#5470c6';
            ctx.fill();
            ctx.strokeStyle = n.id === selected ? '#ffcf33' : 'rgba(255,255,255,.8)';
            ctx.stroke();

            if (nodes.length <= 10) {
                ctx.fillStyle = document.body.classList.contains('graph-dark') ? '#fff' : '#111';
                ctx.font = '12px monospace';
                ctx.textAlign = 'left';
                ctx.fillText(n.label || '', p.x + r + 4, p.y - r);
            }
        });
    }

    function render() {
        const rect = canvas.getBoundingClientRect();
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        if (canvas.width !== Math.floor(rect.width * dpr) || canvas.height !== Math.floor(rect.height * dpr)) {
            canvas.width = Math.floor(rect.width * dpr); canvas.height = Math.floor(rect.height * dpr);
        }
        const ctx = canvas.getContext('2d');
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        draw2d(ctx, rect);
    }

    function nodeAt(clientX, clientY) {
        const rect = canvas.getBoundingClientRect();
        const x = clientX - rect.left, y = clientY - rect.top;
        let hit = null, distance = 12;
        nodes.forEach(n => {
            const p = screenPoint(n);
            const d = Math.hypot(p.x - x, p.y - y);
            if (d < distance) { hit = n; distance = d; }
        });
        return hit;
    }

    function showNode(n) {
        const tooltip = document.getElementById('custom-tooltip');
        if (!tooltip || !n) { if (tooltip) tooltip.style.display = 'none'; return; }
        const authors = (n.authors_raw || []).map(a => (n.uga_authors || []).includes(a.id)
            ? `<span class="uga-author-red">${escapeHtml(a.name)}</span>` : escapeHtml(a.name)).join(', ');
        const labs = (n.uga_labs || (n.uga_lab ? n.uga_lab.split(', ') : [])).join(', ');
        tooltip.innerHTML = `<b>${escapeHtml(n.label)}</b>${labs ? `<br><span class="uga-author-red">Labs:</span> ${escapeHtml(labs)}` : ''}<br>${authors}`;
        tooltip.style.display = 'block';
    }

    canvas.addEventListener('mousemove', e => {
        if (dragging) {
            view.x += e.clientX - dragStart.x; view.y += e.clientY - dragStart.y;
            dragStart = { x: e.clientX, y: e.clientY }; return;
        }
        hovered = nodeAt(e.clientX, e.clientY);
        canvas.style.cursor = hovered ? 'pointer' : 'grab';
        showNode(hovered);
        const tooltip = document.getElementById('custom-tooltip');
        if (tooltip && hovered) { tooltip.style.left = `${e.pageX + 15}px`; tooltip.style.top = `${e.pageY + 15}px`; }
    });
    canvas.addEventListener('mousedown', e => { dragging = true; dragStart = { x: e.clientX, y: e.clientY }; });
    window.addEventListener('mouseup', () => { dragging = false; });
    canvas.addEventListener('mouseleave', () => { if (!selected) hovered = null; });
    canvas.addEventListener('click', e => {
        const hit = nodeAt(e.clientX, e.clientY);
        selected = hit ? hit.id : null;
        hovered = hit;
        showNode(hit);
    });
    canvas.addEventListener('wheel', e => {
        e.preventDefault();
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left, my = e.clientY - rect.top;
        const old = view.scale;
        view.scale *= Math.exp(-e.deltaY * 0.001);
        view.scale = Math.max(0.05, Math.min(20, view.scale));
        view.x = mx - (mx - view.x) * (view.scale / old);
        view.y = my - (my - view.y) * (view.scale / old);
    }, { passive: false });
    window.addEventListener('resize', fit);

    init();
})();
