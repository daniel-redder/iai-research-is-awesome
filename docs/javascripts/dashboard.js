(function () {
    const stopWords = new Set("a about above after again against all am an and any are as at be because been before being below between both but by can could did do does doing down during each few for from further had has have having he her here hers herself him himself his how i if in into is it its itself just me more most my myself no nor not of off on once only or other our ours ourselves out over own same she should so some such than that the their theirs them themselves then there these they this those through to too under until up us very was we were what when where which while who whom why with you your yours yourself yourselves and also using based study model models data research work paper papers".split(/\s+/));

    function abstractText(paper) {
        const abstract = paper.abstract;
        if (typeof abstract === 'string') return abstract;
        if (abstract && typeof abstract === 'object') {
            const words = [];
            Object.entries(abstract).forEach(([word, positions]) => {
                positions.forEach(position => { words[position] = word; });
            });
            return words.filter(Boolean).join(' ');
        }
        return paper.label || '';
    }

    async function loadGraphData() {
        const candidates = [
            new URL('../graph_data.json', window.location.href),
            new URL('graph_data.json', window.location.href),
            new URL('/graph_data.json', window.location.origin)
        ];
        for (const url of [...new Set(candidates.map(candidate => candidate.href))]) {
            try {
                const response = await fetch(url);
                if (response.ok) return response.json();
            } catch (error) { }
        }
        throw new Error('Graph data could not be loaded');
    }

    loadGraphData().then(data => {
        const papers = data.nodes.filter(node => node.group === 'paper');

        const countEl = document.getElementById('repo-paper-count');
        if (countEl) countEl.textContent = papers.length.toLocaleString();

        const densityChart = document.getElementById('publication-density-chart');
        if (densityChart) {
            const countsByDate = new Map();
            papers.forEach(paper => {
                if (paper.publication_date) {
                    countsByDate.set(paper.publication_date, (countsByDate.get(paper.publication_date) || 0) + 1);
                }
            });

            const dates = [...countsByDate.keys()].sort();
            if (dates.length) {
                const start = new Date(dates[0] + 'T00:00:00');
                const end = new Date(dates[dates.length - 1] + 'T00:00:00');
                const cursor = new Date(start);
                cursor.setDate(cursor.getDate() - cursor.getDay());

                let html = '<div class="density-grid">';
                const weeks = [];
                while (cursor <= end) {
                    if (cursor.getDay() === 0) weeks.push([]);
                    const key = cursor.toISOString().slice(0, 10);
                    const count = countsByDate.get(key) || 0;
                    weeks[weeks.length - 1].push({ key, count });
                    cursor.setDate(cursor.getDate() + 1);
                }

                for (let row = 0; row < 7; row++) {
                    for (let column = 0; column < weeks.length; column++) {
                        const value = weeks[column][row];
                        if (!value) html += '<i class="density-empty"></i>';
                        else {
                            const level = value.count === 0 ? 0 : value.count === 1 ? 2 : 4;
                            html += `<i class="density-cell density-level-${level}" title="${value.key}: ${value.count} paper${value.count === 1 ? '' : 's'}"></i>`;
                        }
                    }
                }
                densityChart.innerHTML = html + '</div>';

                const densityGrid = densityChart.querySelector('.density-grid');
                function fitDensityGrid() {
                    if (!densityGrid) return;
                    const availableWidth = Math.max(1, densityChart.clientWidth - 8);
                    const weekCount = Math.max(1, weeks.length);
                    const gap = availableWidth < 500 ? 1 : 3;
                    const cellSize = Math.max(3, Math.floor((availableWidth - gap * (weekCount - 1)) / weekCount));
                    const fittedSize = Math.min(10, cellSize);
                    densityGrid.style.gridAutoColumns = `${fittedSize}px`;
                    densityGrid.style.gridTemplateRows = `repeat(7, ${fittedSize}px)`;
                    densityGrid.style.gap = `${gap}px`;
                    densityGrid.style.width = 'max-content';
                    densityGrid.querySelectorAll('.density-cell, .density-empty').forEach(cell => {
                        cell.style.width = `${fittedSize}px`;
                        cell.style.height = `${fittedSize}px`;
                    });
                }
                fitDensityGrid();
                if ('ResizeObserver' in window) {
                    const observer = new ResizeObserver(fitDensityGrid);
                    observer.observe(densityChart);
                } else {
                    window.addEventListener('resize', fitDensityGrid);
                }

                const detail = document.getElementById('density-hover-detail');
                densityChart.querySelectorAll('.density-cell').forEach(cell => {
                    const date = cell.title.split(':')[0];
                    const matchingPapers = papers.filter(paper => paper.publication_date === date);
                    const showDetail = () => {
                        if (!detail) return;
                        const titles = matchingPapers.map(paper => paper.label).join('<br>');
                        detail.innerHTML = matchingPapers.length
                            ? `<strong>${date}</strong> · ${matchingPapers.length} paper${matchingPapers.length === 1 ? '' : 's'}<br>${titles}`
                            : `<strong>${date}</strong> · No papers`;
                    };
                    cell.setAttribute('tabindex', '0');
                    cell.addEventListener('mouseenter', showDetail);
                    cell.addEventListener('focus', showDetail);
                    cell.addEventListener('mouseleave', () => { if (detail) detail.innerHTML = ''; });
                    cell.addEventListener('blur', () => { if (detail) detail.innerHTML = ''; });
                });
            }
        }

        const wordCounts = new Map();
        const wordPapers = new Map();
        papers.forEach(paper => {
            const text = `${paper.label || ''} ${abstractText(paper)}`;
            const uniqueWords = new Set();
            text.toLowerCase().replace(/[^a-z0-9'-]+/g, ' ').split(/\s+/).forEach(word => {
                word = word.replace(/^['-]+|['-]+$/g, '');
                if (word.length >= 3 && !stopWords.has(word)) {
                    wordCounts.set(word, (wordCounts.get(word) || 0) + 1);
                    uniqueWords.add(word);
                }
            });
            uniqueWords.forEach(word => {
                if (!wordPapers.has(word)) wordPapers.set(word, []);
                wordPapers.get(word).push(paper);
            });
        });

        const topWords = [...wordCounts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 15);
        const cloud = document.getElementById('word-cloud');
        const wordPaperList = document.getElementById('word-paper-list');
        if (cloud) {
            const max = topWords[0]?.[1] || 1;
            topWords.forEach(([word, count], index) => {
                const span = document.createElement('span');
                span.className = 'cloud-word';
                span.textContent = word;
                const scale = 0.75 + 1.5 * Math.sqrt(count / max);
                span.style.fontSize = `${Math.round(12 * scale)}px`;
                span.style.transform = `rotate(${index % 7 === 0 ? -4 : index % 7 === 3 ? 3 : 0}deg)`;
                span.style.opacity = String(0.65 + 0.35 * (count / max));
                span.addEventListener('mouseenter', () => {
                    const matches = wordPapers.get(word) || [];
                    wordPaperList.innerHTML = `<strong>${word}</strong> · ${matches.length} paper${matches.length === 1 ? '' : 's'}<ul>${matches.map(paper => `<li>${paper.label}</li>`).join('')}</ul>`;
                });
                span.addEventListener('mouseleave', () => { wordPaperList.innerHTML = ''; });
                cloud.appendChild(span);
            });
        }

        const chart = document.getElementById('cluster-year-chart');
        if (chart) {
            const datedPapers = papers.filter(paper => /^\d{4}-\d{2}-\d{2}$/.test(paper.publication_date || ''));
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            const windows = [];
            for (let offset = 0; offset < 5; offset++) {
                const end = new Date(today);
                end.setFullYear(end.getFullYear() - offset);
                const start = new Date(end);
                start.setFullYear(start.getFullYear() - 1);
                start.setDate(start.getDate() + 1);
                windows.push({
                    start,
                    end,
                    label: `${start.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })} – ${end.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}`
                });
            }

            let windowIndex = 0;

            function renderYear(direction = 0) {
                const window = windows[windowIndex];
                const counts = new Map();
                datedPapers.forEach(paper => {
                    const date = new Date(paper.publication_date + 'T00:00:00');
                    if (date >= window.start && date <= window.end) {
                        const cluster = paper.cluster_name || 'Unassigned';
                        counts.set(cluster, (counts.get(cluster) || 0) + 1);
                    }
                });

                const entries = [...counts.entries()].sort((a, b) => b[1] - a[1]);
                const max = Math.max(1, ...entries.map(([, value]) => value));
                const title = document.getElementById('year-chart-title');
                if (title) title.textContent = window.label;

                chart.classList.remove('slide-left', 'slide-right');
                void chart.offsetWidth;
                if (direction < 0) chart.classList.add('slide-left');
                if (direction > 0) chart.classList.add('slide-right');
                chart.innerHTML = '';

                function addYearPreview(previewWindow, side) {
                    if (!previewWindow) return;
                    const preview = document.createElement('div');
                    preview.className = `year-preview ${side}`;
                    preview.innerHTML = `<span>${previewWindow.label}</span>`;
                    chart.appendChild(preview);
                }

                addYearPreview(windows[windowIndex + 1], 'previous-year');

                const active = document.createElement('div');
                active.className = 'active-year-bars';
                if (entries.length === 0) {
                    active.innerHTML = '<div class="year-bar-empty">No papers in this period</div>';
                } else {
                    entries.forEach(([cluster, value], index) => {
                        const bar = document.createElement('div');
                        bar.className = 'year-bar';
                        bar.innerHTML = `<div class="year-bar-value">${value}</div><div class="year-bar-fill" style="height:${Math.max(8, 180 * value / max)}px; animation-delay:${index * 45}ms"></div><div class="year-bar-label">${cluster}</div>`;
                        active.appendChild(bar);
                    });
                }
                chart.appendChild(active);

                addYearPreview(windows[windowIndex - 1], 'next-year');

                const previous = document.getElementById('year-chart-prev');
                const next = document.getElementById('year-chart-next');
                if (previous) previous.disabled = windowIndex >= windows.length - 1;
                if (next) next.disabled = windowIndex <= 0;
            }

            const previous = document.getElementById('year-chart-prev');
            const next = document.getElementById('year-chart-next');
            if (previous) previous.addEventListener('click', () => {
                if (windowIndex < windows.length - 1) { windowIndex++; renderYear(-1); }
            });
            if (next) next.addEventListener('click', () => {
                if (windowIndex > 0) { windowIndex--; renderYear(1); }
            });
            renderYear();
        }

        const venueCounts = new Map();
        papers.forEach(paper => {
            const venue = paper.venue && paper.venue !== 'Unknown' ? paper.venue : 'Unknown / Not listed';
            venueCounts.set(venue, (venueCounts.get(venue) || 0) + 1);
        });
        const venueBody = document.getElementById('venue-table-body');
        if (venueBody) {
            const venueRows = [...venueCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 25);
            venueBody.innerHTML = venueRows.length
                ? venueRows.map(([venue, count]) => {
                    const safeVenue = venue.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
                    const venueLink = venue === 'Unknown / Not listed'
                        ? safeVenue
                        : `<a href="https://www.google.com/search?q=${encodeURIComponent(venue)}" target="_blank" rel="noopener">${safeVenue}</a>`;
                    return `<tr><td>${venueLink}</td><td>${count}</td></tr>`;
                }).join('')
                : '<tr><td colspan="2">No publication venues available.</td></tr>';
        }

        function showRandomPaper() {
            if (!papers.length) return;
            const paper = papers[Math.floor(Math.random() * papers.length)];
            const authors = paper.authors_raw ? paper.authors_raw.map(author => author.name).join(', ') : 'Unknown authors';
            const abstract = abstractText(paper);
            const titleEl = document.getElementById('random-paper-title');
            const authorsEl = document.getElementById('random-paper-authors');
            const abstractEl = document.getElementById('random-paper-abstract');
            const link = document.getElementById('random-paper-link');
            if (titleEl) titleEl.textContent = paper.label || 'Untitled paper';
            if (authorsEl) authorsEl.textContent = authors;
            if (abstractEl) abstractEl.textContent = abstract || 'Abstract unavailable.';
            if (link) {
                if (paper.url) {
                    link.href = paper.url;
                    link.style.display = 'inline-block';
                } else {
                    link.style.display = 'none';
                }
            }
        }

        showRandomPaper();
        const shuffle = document.getElementById('shuffle-paper');
        if (shuffle) shuffle.addEventListener('click', showRandomPaper);
    }).catch(error => console.error('Dashboard load failed:', error));
})();
