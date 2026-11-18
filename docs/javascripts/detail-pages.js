(function () {
    function normalizeName(name) {
        return String(name || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
    }

    function sanitizeQueryValue(value) {
        return String(value || "").slice(0, 512);
    }

    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>"']/g, function (char) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;",
            }[char];
        });
    }

    function decodeAbstract(abstract) {
        if (typeof abstract === "string") return abstract;
        if (!abstract || typeof abstract !== "object") return "Abstract unavailable.";
        var words = [];
        Object.entries(abstract).forEach(function (entry) {
            var token = entry[0];
            var positions = entry[1] || [];
            positions.forEach(function (pos) {
                words[pos] = token;
            });
        });
        return words.filter(Boolean).join(" ") || "Abstract unavailable.";
    }

    function safeExternalUrl(value) {
        if (!value) return "";
        try {
            var url = new URL(String(value), window.location.origin);
            if (url.protocol === "http:" || url.protocol === "https:") {
                return url.href;
            }
        } catch (error) {
            return "";
        }
        return "";
    }

    function pageUrl(pageName, params) {
        var url = new URL("../" + pageName + "/", window.location.href);
        if (params) {
            Object.entries(params).forEach(function (entry) {
                if (entry[1] !== undefined && entry[1] !== null && String(entry[1]).length > 0) {
                    url.searchParams.set(entry[0], entry[1]);
                }
            });
        }
        return url.toString();
    }

    function loadGraphData() {
        var candidates = [
            new URL("../graph_data.json", window.location.href),
            new URL("graph_data.json", window.location.href),
            new URL("/graph_data.json", window.location.origin),
        ];

        var uniqueUrls = Array.from(new Set(candidates.map(function (candidate) { return candidate.href; })));
        return uniqueUrls.reduce(function (promise, url) {
            return promise.catch(function () {
                return fetch(url).then(function (response) {
                    if (!response.ok) throw new Error("not found");
                    return response.json();
                });
            });
        }, Promise.reject(new Error("not loaded yet")));
    }

    function renderClusterPage(data, params) {
        var clusterName = sanitizeQueryValue(params.get("name") || "");
        var titleEl = document.getElementById("cluster-title");
        var countEl = document.getElementById("cluster-count");
        var tbody = document.getElementById("cluster-table-body");

        if (!clusterName) {
            titleEl.textContent = "Missing cluster name";
            tbody.innerHTML = '<tr><td colspan="4">Add ?name=Cluster%20Name to the URL.</td></tr>';
            return;
        }

        var selectedYear = localStorage.getItem("uga-selected-year") || String(new Date().getFullYear());
        var papers = data.nodes
            .filter(function (node) { return node.group === "paper" && node.cluster_name === clusterName; })
            .filter(function (node) {
                var paperYear = new Date(node.publication_date).getFullYear();
                return paperYear === Number(selectedYear);
            })
            .sort(function (a, b) { return String(b.publication_date || "").localeCompare(String(a.publication_date || "")); });

        titleEl.textContent = clusterName;
        countEl.textContent = papers.length + " paper" + (papers.length === 1 ? "" : "s");

        if (!papers.length) {
            tbody.innerHTML = '<tr><td colspan="4">No papers found for this cluster.</td></tr>';
            return;
        }

        tbody.innerHTML = papers.map(function (paper) {
            var authors = (paper.authors_raw || []).map(function (author) {
                var authorName = author && author.name ? author.name : "Unknown";
                var authorId = author && author.id ? author.id : "";
                var href = pageUrl("author", { name: normalizeName(authorName), id: authorId });
                return '<a href="' + href + '">' + escapeHtml(authorName) + "</a>";
            }).join(", ");

            return "<tr>" +
                '<td><a href="' + pageUrl("paper", { id: paper.id }) + '">' + escapeHtml(paper.label || "Untitled") + "</a></td>" +
                "<td>" + escapeHtml(paper.publication_date || "Unknown") + "</td>" +
                "<td>" + authors + "</td>" +
                "<td>" + escapeHtml(paper.venue || "Unknown") + "</td>" +
                "</tr>";
        }).join("");
    }

    function renderPaperPage(data, params) {
        var paperId = sanitizeQueryValue(params.get("id") || "");
        var paper = data.nodes.find(function (node) { return node.group === "paper" && node.id === paperId; });
        var body = document.getElementById("paper-body");

        if (!paper) {
            body.innerHTML = '<p>Paper not found. Add ?id=https://openalex.org/W... to the URL.</p>';
            return;
        }

        var authorsHtml = (paper.authors_raw || []).map(function (author) {
            var authorName = author && author.name ? author.name : "Unknown";
            var authorId = author && author.id ? author.id : "";
            var href = pageUrl("author", { name: normalizeName(authorName), id: authorId });
            return '<li><a href="' + href + '">' + escapeHtml(authorName) + "</a>" +
                (authorId ? ' <span class="meta">(' + escapeHtml(authorId) + ")</span>" : "") +
                "</li>";
        }).join("");

        var externalPaperUrl = safeExternalUrl(paper.url);

        body.innerHTML = "" +
            "<h1>" + escapeHtml(paper.label || "Untitled") + "</h1>" +
            '<div class="meta-grid">' +
            '<div><strong>Publication date:</strong> ' + escapeHtml(paper.publication_date || "Unknown") + "</div>" +
            '<div><strong>Cluster:</strong> <a href="' + pageUrl("cluster", { name: paper.cluster_name || "Unassigned" }) + '">' + escapeHtml(paper.cluster_name || "Unassigned") + "</a></div>" +
            '<div><strong>Venue:</strong> ' + escapeHtml(paper.venue || "Unknown") + "</div>" +
            '<div><strong>OpenAlex ID:</strong> ' + escapeHtml(paper.id || "Unknown") + "</div>" +
            (externalPaperUrl ? '<div><strong>Publication URL:</strong> <a href="' + escapeHtml(externalPaperUrl) + '" target="_blank" rel="noopener">Open paper</a></div>' : "") +
            "</div>" +
            "<h2>Authors</h2>" +
            (authorsHtml ? "<ul>" + authorsHtml + "</ul>" : "<p>Unknown authors.</p>") +
            "<h2>Abstract</h2>" +
            "<p>" + escapeHtml(decodeAbstract(paper.abstract)) + "</p>";
    }

    function renderAuthorPage(data, params) {
        var requestedName = normalizeName(sanitizeQueryValue(params.get("name") || ""));
        var requestedId = sanitizeQueryValue(params.get("id") || "");
        var body = document.getElementById("author-body");

        var papers = data.nodes.filter(function (node) { return node.group === "paper"; });
        var authorNodes = new Map(
            data.nodes
                .filter(function (node) { return node.group === "author"; })
                .map(function (node) { return [node.id, node]; })
        );

        var mentionsByName = new Map();

        papers.forEach(function (paper) {
            var ugaSet = new Set(paper.uga_authors || []);
            (paper.authors_raw || []).forEach(function (author) {
                var name = author && author.name ? author.name : "";
                var normalized = normalizeName(name);
                if (!normalized) return;

                if (!mentionsByName.has(normalized)) {
                    mentionsByName.set(normalized, {
                        names: new Set(),
                        ids: new Set(),
                        ugaIds: new Set(),
                        publications: new Map(),
                    });
                }

                var bucket = mentionsByName.get(normalized);
                var authorId = author && author.id ? author.id : "";

                bucket.names.add(name || "Unknown author");
                if (authorId) bucket.ids.add(authorId);
                if (authorId && ugaSet.has(authorId)) bucket.ugaIds.add(authorId);

                if (!bucket.publications.has(paper.id)) {
                    bucket.publications.set(paper.id, {
                        paper: paper,
                        authorIds: new Set(),
                        hasMissingId: false,
                    });
                }

                var publicationEntry = bucket.publications.get(paper.id);
                if (authorId) publicationEntry.authorIds.add(authorId);
                else publicationEntry.hasMissingId = true;
            });
        });

        var resolvedName = requestedName;
        if (!resolvedName && requestedId) {
            mentionsByName.forEach(function (bucket, key) {
                if (bucket.ids.has(requestedId)) resolvedName = key;
            });
        }

        if (!resolvedName) {
            body.innerHTML = '<p>Author not found. Add ?name=normalized%20name or ?id=https://openalex.org/A...</p>';
            return;
        }

        var authorBucket = mentionsByName.get(resolvedName);
        if (!authorBucket) {
            body.innerHTML = '<p>No records found for this author query.</p>';
            return;
        }

        var rosterIds = new Set(authorBucket.ugaIds);
        var allIds = Array.from(authorBucket.ids);
        var displayIds;
        var groupLabel;

        if (rosterIds.size > 0) {
            if (requestedId && !rosterIds.has(requestedId)) {
                displayIds = allIds.filter(function (authorId) { return !rosterIds.has(authorId); });
                groupLabel = "External same-name merged entity";
                if (!displayIds.length) {
                    displayIds = Array.from(rosterIds);
                    groupLabel = "Roster-confirmed author entity";
                }
            } else {
                displayIds = Array.from(rosterIds);
                groupLabel = "Roster-confirmed author entity";
            }
        } else {
            displayIds = allIds;
            groupLabel = "Merged same-name author entity";
        }

        var displayIdSet = new Set(displayIds);

        var publications = Array.from(authorBucket.publications.values())
            .filter(function (entry) {
                if (!displayIds.length) return true;
                if (entry.hasMissingId) return true;
                return Array.from(entry.authorIds).some(function (authorId) { return displayIdSet.has(authorId); });
            })
            .map(function (entry) { return entry.paper; })
            .sort(function (a, b) { return String(b.publication_date || "").localeCompare(String(a.publication_date || "")); });

        var representativeName = Array.from(authorBucket.names).sort(function (a, b) {
            return b.length - a.length;
        })[0] || resolvedName;

        var metadataSource = displayIds
            .map(function (id) { return authorNodes.get(id); })
            .find(function (node) { return node && (node.roster_title || node.roster_status || node.roster_profile_url); });

        var title = metadataSource && metadataSource.roster_title ? metadataSource.roster_title : "Unknown";
        var affiliation = "Unknown";
        if (metadataSource && metadataSource.roster_title) {
            var pieces = String(metadataSource.roster_title).split(",").map(function (p) { return p.trim(); }).filter(Boolean);
            affiliation = pieces.slice(1).join(", ") || pieces[0] || "Unknown";
        }

        var publicationRows = publications.map(function (paper) {
            return "<tr>" +
                '<td><a href="' + pageUrl("paper", { id: paper.id }) + '">' + escapeHtml(paper.label || "Untitled") + "</a></td>" +
                "<td>" + escapeHtml(paper.publication_date || "Unknown") + "</td>" +
                '<td><a href="' + pageUrl("cluster", { name: paper.cluster_name || "Unassigned" }) + '">' + escapeHtml(paper.cluster_name || "Unassigned") + "</a></td>" +
                "</tr>";
        }).join("");

        var externalProfileUrl = metadataSource ? safeExternalUrl(metadataSource.roster_profile_url) : "";

        body.innerHTML = "" +
            "<h1>" + escapeHtml(representativeName) + "</h1>" +
            '<div class="meta-grid">' +
            "<div><strong>Entity type:</strong> " + escapeHtml(groupLabel) + "</div>" +
            "<div><strong>Title:</strong> " + escapeHtml(title) + "</div>" +
            "<div><strong>Affiliation:</strong> " + escapeHtml(affiliation) + "</div>" +
            "<div><strong>Roster status:</strong> " + escapeHtml((metadataSource && metadataSource.roster_status) || "Uncertain") + "</div>" +
            (externalProfileUrl ? "<div><strong>Profile:</strong> <a href=\"" + escapeHtml(externalProfileUrl) + "\" target=\"_blank\" rel=\"noopener\">Directory profile</a></div>" : "") +
            "</div>" +
            "<h2>Stacked IDs</h2>" +
            (displayIds.length
                ? "<ul>" + displayIds.map(function (id) { return "<li>" + escapeHtml(id) + "</li>"; }).join("") + "</ul>"
                : "<p>No author IDs available.</p>") +
            "<h2>Publications in this dataset</h2>" +
            (publications.length
                ? '<table class="detail-table"><thead><tr><th>Title</th><th>Date</th><th>Cluster</th></tr></thead><tbody>' + publicationRows + "</tbody></table>"
                : "<p>No publications found for this merged author entity.</p>");
    }

    function init() {
        var container = document.getElementById("detail-page");
        if (!container) return;

        var pageType = container.getAttribute("data-page");
        var params = new URLSearchParams(window.location.search);

        loadGraphData()
            .then(function (data) {
                if (pageType === "cluster") renderClusterPage(data, params);
                else if (pageType === "paper") renderPaperPage(data, params);
                else if (pageType === "author") renderAuthorPage(data, params);
            })
            .catch(function (error) {
                container.innerHTML = '<p>Could not load graph data: ' + escapeHtml(error.message) + "</p>";
            });
    }

    init();
})();
