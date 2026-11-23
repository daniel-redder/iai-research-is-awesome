(function () {
    const stopWords = new Set("a about above after again against all am an and any are as at be because been before being below between both but by can could did do does doing down during each few for from further had has have having he her here hers herself him himself his how i if in into is it its itself just me more most my myself no nor not of off on once only or other our ours ourselves out over own same she should so some such than that the their theirs them themselves then there these they this those through to too under until up us very was we were what when where which while who whom why with you your yours yourself yourselves and also using based study model models data research work works paper papers across method methods existing result results framework evaluation accuracy propose design".split(/\s+/));

    stopWords.add('thi');

    const commonTerms = [
        { label: 'large language models', regex: /\blarge language models?\b/g },
        { label: 'reinforcement learning', regex: /\breinforcement learning\b/g },
        { label: 'multi-agent systems', regex: /\bmulti[- ]agent systems?\b/g },
        { label: 'computer vision', regex: /\bcomputer vision\b/g },
        { label: 'natural language processing', regex: /\bnatural language processing\b|\bnlp\b/g },
        { label: 'knowledge graph', regex: /\bknowledge graphs?\b/g },
        { label: 'federated learning', regex: /\bfederated learning\b/g },
        { label: 'graph neural networks', regex: /\bgraph neural networks?\b|\bgnns?\b/g },
        { label: 'machine learning', regex: /\bmachine learning\b/g },
        { label: 'deep learning', regex: /\bdeep learning\b/g },
        { label: 'generative ai', regex: /\bgenerative ai\b/g },
        { label: 'autonomous systems', regex: /\bautonomous systems?\b/g },
    ];

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, c => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[c]));
    }

    function safeExternalUrl(value) {
        if (!value) return '';
        try {
            const url = new URL(String(value), window.location.origin);
            if (url.protocol === 'http:' || url.protocol === 'https:') return url.href;
        } catch (error) {
            return '';
        }
        return '';
    }

    function normalizeName(name) {
        return String(name || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
    }

    function abbreviateLabName(name) {
        const full = String(name || '').trim();
        if (!full) return 'Unknown';
        const words = full.split(/[\s/&,-]+/).filter(Boolean);
        if (words.length >= 2) {
            const acronym = words.map(word => word[0]?.toUpperCase() || '').join('');
            if (acronym.length >= 2 && acronym.length <= 8) return acronym;
        }
        return full.length > 12 ? `${full.slice(0, 11)}…` : full;
    }

    function formatIsoDate(value) {
        if (typeof value !== 'string') return '';
        const match = value.match(/^(\d{4}-\d{2}-\d{2})/);
        return match ? match[1] : '';
    }

    function detailPageUrl(pageName, params) {
        const url = new URL(`${pageName}/`, window.location.href);
        if (params && typeof params === 'object') {
            Object.entries(params).forEach(([key, value]) => {
                if (value !== undefined && value !== null && String(value).length > 0) {
                    url.searchParams.set(key, String(value));
                }
            });
        }
        return url.toString();
    }

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

    function gitIconMarkup() {
        return '<svg class="paper-link-icon" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path fill="currentColor" d="M1 3.75a2.75 2.75 0 1 1 4.095 2.402l2.243 1.495A2.754 2.754 0 0 1 9.75 6h1.5a2.75 2.75 0 1 1 0 1.5h-1.5a1.25 1.25 0 1 0 0 2.5h1.5a2.75 2.75 0 1 1 0 1.5h-1.5A2.75 2.75 0 0 1 7 8.406L4.53 6.76A2.75 2.75 0 1 1 1 3.75Zm2.75-1.25a1.25 1.25 0 1 0 0 2.5 1.25 1.25 0 0 0 0-2.5Zm8.5 5a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5Zm0 5a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5Z"></path></svg>';
    }

    function summarizeAuthors(paper) {
        const names = (paper.authors_raw || []).map(author => author?.name).filter(Boolean);
        if (!names.length) return 'Unknown authors';
        const preview = names.slice(0, 3).join(', ');
        return names.length > 3 ? `${preview}, et. al.` : preview;
    }

    function renderPaperList(title, papers) {
        if (!papers.length) {
            return `<div class="paper-list-header"><strong>${escapeHtml(title)}</strong></div><p class="paper-list-empty">No papers</p>`;
        }
        const rows = papers.map(paper => {
            const safeTitle = escapeHtml(paper.label || 'Untitled paper');
            const safeAuthors = escapeHtml(summarizeAuthors(paper));
            const detailUrl = detailPageUrl('paper', { id: paper.id });
            const titleMarkup = paper.id
                ? `<a class="paper-list-link" href="${detailUrl}">${gitIconMarkup()}<span>${safeTitle}</span></a>`
                : `<span class="paper-list-link is-disabled">${gitIconMarkup()}<span>${safeTitle}</span></span>`;
            return `<article class="paper-list-item">${titleMarkup}<div class="paper-list-authors">${safeAuthors}</div></article>`;
        }).join('');
        return `<div class="paper-list-header"><strong>${escapeHtml(title)}</strong></div><div class="paper-list-items">${rows}</div>`;
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

    async function loadHarvestState() {
        const candidates = [
            new URL('../data/harvest_state.json', window.location.href),
            new URL('data/harvest_state.json', window.location.href),
            new URL('/data/harvest_state.json', window.location.origin),
            new URL('harvest_state.json', window.location.href),
            new URL('/harvest_state.json', window.location.origin)
        ];
        for (const url of [...new Set(candidates.map(candidate => candidate.href))]) {
            try {
                const response = await fetch(url);
                if (response.ok) return response.json();
            } catch (error) { }
        }
        return null;
    }

    Promise.all([loadGraphData(), loadHarvestState()]).then(([data, harvestState]) => {
        const latestSearchDate = formatIsoDate(harvestState?.last_run || harvestState?.forward_cursor || '');
        const latestSearchEl = document.getElementById('repo-commit-date');
        if (latestSearchEl) {
            latestSearchEl.textContent = latestSearchDate || 'Unknown';
        }

        const allPapers = data.nodes.filter(node => node.group === 'paper');
        const years = window.UGAYearFilter.availableYears(allPapers);
        let selectedYear = window.UGAYearFilter.selectedYear(allPapers);

        const yearSelector = document.getElementById('year-selector');
        const yearSelectorLabel = document.getElementById('year-selector-label');
        if (yearSelector) {
            yearSelector.innerHTML = years.map(year => `<option value="${year}">${year}</option>`).join('');
            yearSelector.value = selectedYear;
            yearSelector.addEventListener('change', () => {
                window.UGAYearFilter.setSelectedYear(yearSelector.value);
                window.location.reload();
            });
        }
        if (yearSelectorLabel) yearSelectorLabel.textContent = selectedYear;

        function selectedPapersForYear() {
            return allPapers.filter(paper =>
                typeof paper.publication_date === 'string' &&
                paper.publication_date.startsWith(selectedYear)
            );
        }

        window.addEventListener('uga-year-change', event => {
            selectedYear = event.detail?.year || selectedYear;
            if (yearSelector) yearSelector.value = selectedYear;
            if (yearSelectorLabel) yearSelectorLabel.textContent = selectedYear;
            renderDashboard();
        });

        function renderDashboard() {
            const papers = selectedPapersForYear();
            renderDatabaseWidget(papers);
            renderWordFrequency(papers);
            renderClusterLabChart(papers);
            renderVenueTable(papers);
            showRandomPaper(papers);
        }

        const papersPublishedThisYear = allPapers.filter(paper =>
            typeof paper.publication_date === 'string' &&
            paper.publication_date.startsWith(selectedYear)
        );

        const countEl = document.getElementById('repo-paper-count');
        if (countEl) countEl.textContent = papersPublishedThisYear.length.toLocaleString();

        const densityChart = document.getElementById('publication-density-chart');
        if (densityChart) {
            const countsByDate = new Map();
            papersPublishedThisYear.forEach(paper => {
                if (typeof paper.publication_date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(paper.publication_date)) {
                    countsByDate.set(paper.publication_date, (countsByDate.get(paper.publication_date) || 0) + 1);
                }
            });

            const start = new Date(`${selectedYear}-01-01T00:00:00`);
            const end = new Date(`${selectedYear}-12-31T00:00:00`);
            const cursor = new Date(start);
            cursor.setDate(cursor.getDate() - cursor.getDay());

            let html = '<div class="density-grid">';
            const weeks = [];
            while (cursor <= end) {
                if (cursor.getDay() === 0) weeks.push([]);
                const key = cursor.toISOString().slice(0, 10);
                const count = key.startsWith(`${selectedYear}-`) ? (countsByDate.get(key) || 0) : null;
                weeks[weeks.length - 1].push(count === null ? null : { key, count });
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
                const compactView = availableWidth < 360;
                const gap = compactView ? 2 : availableWidth < 500 ? 1 : 3;
                const cellSize = Math.max(compactView ? 6 : 4, Math.floor((availableWidth - gap * (weekCount - 1)) / weekCount));
                const fittedSize = compactView ? 6 : Math.min(10, cellSize);
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
            let lockedDensityDate = null;
            densityChart.querySelectorAll('.density-cell').forEach(cell => {
                const date = cell.title.split(':')[0];
                const matchingPapers = papersPublishedThisYear.filter(paper => paper.publication_date === date);
                const showDetail = () => {
                    if (!detail) return;
                    const headline = `${date} · ${matchingPapers.length} paper${matchingPapers.length === 1 ? '' : 's'}`;
                    detail.innerHTML = renderPaperList(headline, matchingPapers);
                };
                cell.setAttribute('tabindex', '0');
                cell.addEventListener('mouseenter', () => { if (!lockedDensityDate) showDetail(); });
                cell.addEventListener('focus', () => { if (!lockedDensityDate) showDetail(); });
                cell.addEventListener('mouseleave', () => { if (!lockedDensityDate && detail) detail.innerHTML = ''; });
                cell.addEventListener('blur', () => { if (!lockedDensityDate && detail) detail.innerHTML = ''; });
                cell.addEventListener('click', () => {
                    if (lockedDensityDate === date) {
                        lockedDensityDate = null;
                        cell.classList.remove('active');
                        if (detail) detail.innerHTML = '';
                    } else {
                        densityChart.querySelectorAll('.density-cell.active').forEach(active => active.classList.remove('active'));
                        lockedDensityDate = date;
                        cell.classList.add('active');
                        showDetail();
                    }
                });
            });
        }

        const wordCounts = new Map();
        const wordPapers = new Map();
        papersPublishedThisYear.forEach(paper => {
            const text = `${paper.label || ''} ${abstractText(paper)}`;
            const normalizedText = text.toLowerCase().replace(/[^a-z0-9'\-\s]+/g, ' ');
            const uniqueWords = new Set();

            commonTerms.forEach(term => {
                const matches = normalizedText.match(term.regex);
                if (matches && matches.length) {
                    wordCounts.set(term.label, (wordCounts.get(term.label) || 0) + matches.length);
                    uniqueWords.add(term.label);
                }
            });

            normalizedText.split(/\s+/).forEach(word => {
                word = word.replace(/^['-]+|['-]+$/g, '');
                if (word.endsWith('ies') && word.length > 4) {
                    word = word.slice(0, -3) + 'y';
                } else if (word.endsWith('sses') && word.length > 5) {
                    word = word.slice(0, -2);
                } else if (word.endsWith('s') && word.length > 3 && !word.endsWith('ss')) {
                    word = word.slice(0, -1);
                }
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
            let lockedWord = null;
            const max = topWords[0]?.[1] || 1;

            function showMatches(word) {
                const matches = wordPapers.get(word) || [];
                const headline = `${word} · ${matches.length} paper${matches.length === 1 ? '' : 's'}`;
                wordPaperList.innerHTML = renderPaperList(headline, matches);
            }

            function renderWordCloud() {
                const cloudWidth = Math.max(260, cloud.clientWidth || 0);
                const compactView = cloudWidth < 380;
                const renderWords = compactView ? topWords.slice(0, 10) : topWords;
                const base = compactView
                    ? Math.max(12, Math.min(17, Math.floor(cloudWidth / 22)))
                    : Math.max(11, Math.min(18, Math.floor(cloudWidth / 24)));
                cloud.innerHTML = '';

                renderWords.forEach(([word, count], index) => {
                    const span = document.createElement('span');
                    span.className = 'cloud-word';
                    span.textContent = word;
                    const scale = compactView ? (0.74 + 1.18 * Math.sqrt(count / max)) : (0.75 + 1.4 * Math.sqrt(count / max));
                    span.style.fontSize = `${Math.round(base * scale)}px`;
                    span.style.transform = `rotate(${index % 7 === 0 ? -4 : index % 7 === 3 ? 3 : 0}deg)`;
                    span.style.opacity = String(0.65 + 0.35 * (count / max));
                    span.setAttribute('tabindex', '0');

                    span.addEventListener('mouseenter', () => { if (!lockedWord) showMatches(word); });
                    span.addEventListener('focus', () => { if (!lockedWord) showMatches(word); });
                    span.addEventListener('mouseleave', () => { if (!lockedWord) wordPaperList.innerHTML = ''; });
                    span.addEventListener('blur', () => { if (!lockedWord) wordPaperList.innerHTML = ''; });
                    span.addEventListener('click', () => {
                        if (lockedWord === word) {
                            lockedWord = null;
                            span.classList.remove('active');
                            wordPaperList.innerHTML = '';
                        } else {
                            cloud.querySelectorAll('.cloud-word.active').forEach(active => active.classList.remove('active'));
                            lockedWord = word;
                            span.classList.add('active');
                            showMatches(word);
                        }
                    });

                    if (lockedWord === word) span.classList.add('active');
                    cloud.appendChild(span);
                });
            }

            renderWordCloud();
            if ('ResizeObserver' in window) {
                const cloudObserver = new ResizeObserver(renderWordCloud);
                cloudObserver.observe(cloud);
            } else {
                window.addEventListener('resize', renderWordCloud);
            }
        }

        const chart = document.getElementById('cluster-year-chart');
        if (chart) {
            const clusters = new Map();
            const labs = new Map();
            papersPublishedThisYear.forEach(paper => {
                const cluster = paper.cluster_name || 'Unassigned';
                if (!clusters.has(cluster)) clusters.set(cluster, new Map());
                const paperLabs = new Set((paper.uga_labs || []).filter(Boolean));
                paperLabs.forEach(lab => {
                    const counts = clusters.get(cluster);
                    counts.set(lab, (counts.get(lab) || 0) + 1);
                    labs.set(lab, (labs.get(lab) || 0) + 1);
                });
            });

            chart.innerHTML = '';
            chart.classList.add('cluster-lab-heatmap');

            if (!clusters.size) {
                chart.innerHTML = '<p class="heatmap-empty">No papers in this year.</p>';
            } else if (!labs.size) {
                chart.innerHTML = '<p class="heatmap-empty">No UGA lab affiliations are listed for this year.</p>';
            } else {
                const clusterList = [...clusters.entries()].sort((a, b) => a[0].localeCompare(b[0]));
                const labList = [...labs.keys()].sort((a, b) => a.localeCompare(b));
                const useCompactLabLabels = window.matchMedia('(max-width: 62rem)').matches;
                const maxCount = Math.max(...clusterList.flatMap(([, counts]) => [...counts.values()]));
                const table = document.createElement('table');
                table.className = 'cluster-lab-heatmap-table';
                table.style.tableLayout = 'fixed';

                const head = document.createElement('thead');
                const headingRow = document.createElement('tr');
                const labHeading = document.createElement('th');
                labHeading.scope = 'col';
                labHeading.textContent = 'Lab';
                headingRow.appendChild(labHeading);
                clusterList.forEach(([cluster]) => {
                    const heading = document.createElement('th');
                    heading.scope = 'col';
                    heading.textContent = cluster;
                    headingRow.appendChild(heading);
                });
                head.appendChild(headingRow);
                table.appendChild(head);

                const body = document.createElement('tbody');
                labList.forEach(lab => {
                    const row = document.createElement('tr');
                    const label = document.createElement('th');
                    label.scope = 'row';
                    const compactLabName = abbreviateLabName(lab);
                    label.textContent = useCompactLabLabels ? compactLabName : lab;
                    label.title = lab;
                    label.setAttribute('aria-label', lab);
                    row.appendChild(label);

                    clusterList.forEach(([cluster, counts]) => {
                        const count = counts.get(lab) || 0;
                        const cell = document.createElement('td');
                        const level = count ? Math.max(1, Math.ceil((count / maxCount) * 5)) : 0;
                        cell.className = `heatmap-cell heatmap-level-${level}`;
                        cell.textContent = count ? String(count) : '';
                        cell.title = `${lab} · ${cluster}: ${count} paper${count === 1 ? '' : 's'}`;
                        cell.setAttribute('aria-label', cell.title);
                        row.appendChild(cell);
                    });
                    body.appendChild(row);
                });
                table.appendChild(body);

                const scroll = document.createElement('div');
                scroll.className = 'cluster-lab-heatmap-scroll';
                scroll.appendChild(table);
                chart.appendChild(scroll);

                const legend = document.createElement('div');
                legend.className = 'heatmap-legend';
                legend.innerHTML = '<span>Fewer papers</span><i class="heatmap-level-1"></i><i class="heatmap-level-3"></i><i class="heatmap-level-5"></i><span>More papers</span>';
                chart.appendChild(legend);
            }
        }

        const venueCounts = new Map();
        papersPublishedThisYear.forEach(paper => {
            const venue = paper.venue && paper.venue !== 'Unknown' ? paper.venue : 'Unknown / Not listed';
            venueCounts.set(venue, (venueCounts.get(venue) || 0) + 1);
        });
        const venueBody = document.getElementById('venue-table-body');
        if (venueBody) {
            const venueRows = [...venueCounts.entries()].sort((a, b) => b[1] - a[1]);
            venueBody.innerHTML = venueRows.length
                ? venueRows.map(([venue, count]) => {
                    const safeVenue = venue.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
                    return `<tr><td>${safeVenue}</td><td>${count}</td></tr>`;
                }).join('')
                : '<tr><td colspan="2">No publication venues available.</td></tr>';
        }

        function showRandomPaper() {
            if (!papersPublishedThisYear.length) return;
            const paper = papersPublishedThisYear[Math.floor(Math.random() * papersPublishedThisYear.length)];
            const abstract = abstractText(paper);
            const titleEl = document.getElementById('random-paper-title');
            const publicationEl = document.getElementById('random-paper-publication-date');
            const scanDateEl = document.getElementById('random-paper-scan-date');
            const authorsEl = document.getElementById('random-paper-authors');
            const abstractEl = document.getElementById('random-paper-abstract');
            const link = document.getElementById('random-paper-link');
            if (titleEl) titleEl.textContent = paper.label || 'Untitled paper';
            if (publicationEl) publicationEl.textContent = formatIsoDate(paper.publication_date) || 'Unknown';
            if (scanDateEl) scanDateEl.textContent = latestSearchDate || 'Unknown';
            if (authorsEl) {
                authorsEl.replaceChildren();
                const ugaAuthors = new Set(paper.uga_authors || []);
                (paper.authors_raw || []).forEach((author, index) => {
                    if (index) authorsEl.append(document.createTextNode(', '));
                    const isUgaAuthor = ugaAuthors.has(author.id);
                    const authorName = author?.name || 'Unknown';
                    const authorId = author?.id || '';
                    const authorHref = detailPageUrl('author', { name: normalizeName(authorName), id: authorId });
                    const authorLink = document.createElement('a');
                    authorLink.href = authorHref;
                    authorLink.textContent = authorName;
                    if (isUgaAuthor) authorLink.className = 'uga-author-name';
                    authorsEl.append(authorLink);
                });
                if (!paper.authors_raw || !paper.authors_raw.length) authorsEl.textContent = 'Unknown authors';
            }
            if (abstractEl) abstractEl.textContent = abstract || 'Abstract unavailable.';
            if (link) {
                const detailUrl = paper.id ? detailPageUrl('paper', { id: paper.id }) : '';
                if (detailUrl) {
                    link.href = detailUrl;
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
