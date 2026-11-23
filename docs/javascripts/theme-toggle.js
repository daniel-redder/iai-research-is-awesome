(function () {
    var STORAGE_KEY = "uga-theme";
    var themeScriptUrl = document.currentScript && document.currentScript.src
        ? document.currentScript.src
        : new URL("javascripts/theme-toggle.js", window.location.href).href;
    var siteRootUrl = new URL("../", themeScriptUrl);

    function getSystemTheme() {
        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }

    function getPreferredTheme() {
        var saved = window.localStorage.getItem(STORAGE_KEY);
        if (saved === "dark" || saved === "light") {
            return saved;
        }
        return getSystemTheme();
    }

    function applyTheme(theme) {
        document.body.classList.remove("uga-theme-light", "uga-theme-dark");
        document.body.classList.add(theme === "dark" ? "uga-theme-dark" : "uga-theme-light");
    }

    function iconForTheme(theme) {
        return theme === "dark" ? "☀" : "☾";
    }

    function labelForTheme(theme) {
        return theme === "dark" ? "Light" : "Dark";
    }

    function setButtonState(button, activeTheme) {
        button.querySelector(".theme-toggle-icon").textContent = iconForTheme(activeTheme);
        button.querySelector(".theme-toggle-label").textContent = labelForTheme(activeTheme);
        button.setAttribute("aria-label", "Switch to " + labelForTheme(activeTheme) + " mode");
    }

    function buildToggle() {
        var menu = document.querySelector(".terminal-menu > ul");
        if (!menu || document.querySelector(".theme-toggle-item")) {
            return;
        }

        var item = document.createElement("li");
        item.className = "theme-toggle-item";
        item.setAttribute("property", "itemListElement");
        item.setAttribute("typeof", "ListItem");

        var button = document.createElement("button");
        button.type = "button";
        button.className = "theme-toggle-btn";
        button.innerHTML = '<span class="theme-toggle-icon" aria-hidden="true"></span><span class="theme-toggle-label"></span>';

        var activeTheme = getPreferredTheme();
        applyTheme(activeTheme);
        setButtonState(button, activeTheme);

        button.addEventListener("click", function () {
            var nextTheme = document.body.classList.contains("uga-theme-dark") ? "light" : "dark";
            applyTheme(nextTheme);
            window.localStorage.setItem(STORAGE_KEY, nextTheme);
            setButtonState(button, nextTheme);
        });

        item.appendChild(button);
        menu.appendChild(item);

        if (!document.querySelector(".github-header-item")) {
            var githubItem = document.createElement("li");
            githubItem.className = "github-header-item";
            githubItem.setAttribute("property", "itemListElement");
            githubItem.setAttribute("typeof", "ListItem");

            var githubLink = document.createElement("a");
            githubLink.href = "https://github.com/daniel-redder/iai-research-is-awesome";
            githubLink.target = "_blank";
            githubLink.rel = "noopener";
            githubLink.className = "github-header-link";
            githubLink.title = "View source on GitHub";
            githubLink.setAttribute("aria-label", "View source on GitHub");
            githubLink.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M23.546 10.93 13.07.454a1.551 1.551 0 0 0-2.194 0l-2.18 2.18 2.766 2.766a1.84 1.84 0 0 1 2.33 2.345l2.666 2.666a1.84 1.84 0 1 1-1.104 1.036l-2.486-2.487v6.548a1.84 1.84 0 1 1-1.522 0V8.9a1.84 1.84 0 0 1-.999-2.414L7.62 3.733.454 10.9a1.551 1.551 0 0 0 0 2.194l10.476 10.476a1.551 1.551 0 0 0 2.194 0l10.422-10.422a1.551 1.551 0 0 0 0-2.194"/></svg>';

            githubItem.appendChild(githubLink);
            menu.appendChild(githubItem);
        }
    }

    function buildYearSelector(siteName) {
        if (document.querySelector(".header-year-control")) return;

        var control = document.createElement("div");
        control.className = "header-year-control";
        control.innerHTML = "" +
            '<button type="button" class="header-year-trigger" aria-expanded="false" aria-controls="header-year-menu">' +
            '<span>YEAR</span><strong class="header-year-value"></strong><span aria-hidden="true">&#9662;</span>' +
            "</button>" +
            '<div class="header-year-menu" id="header-year-menu" role="group" aria-label="Select publication year" hidden>' +
            '<button type="button" class="header-year-step" data-step="-1" aria-label="Newer year" title="Newer year">&#9650;</button>' +
            '<select class="header-year-select" aria-label="Publication year"></select>' +
            '<button type="button" class="header-year-step" data-step="1" aria-label="Older year" title="Older year">&#9660;</button>' +
            "</div>";

        var trigger = control.querySelector(".header-year-trigger");
        var value = control.querySelector(".header-year-value");
        var menu = control.querySelector(".header-year-menu");
        var select = control.querySelector(".header-year-select");
        var stepButtons = control.querySelectorAll(".header-year-step");
        var selectedYear = window.localStorage.getItem("uga-selected-year") || String(new Date().getFullYear());
        var years = [selectedYear];

        function refreshControls() {
            var selectedIndex = years.indexOf(select.value);
            stepButtons.forEach(function (button) {
                var nextIndex = selectedIndex + Number(button.getAttribute("data-step"));
                button.disabled = nextIndex < 0 || nextIndex >= years.length;
            });
        }

        function applyYear(year) {
            if (window.UGAYearFilter) window.UGAYearFilter.setSelectedYear(year);
            else window.localStorage.setItem("uga-selected-year", String(year));
            window.location.reload();
        }

        function renderYears(availableYears) {
            years = availableYears.length ? availableYears : [selectedYear];
            select.innerHTML = years.map(function (year) {
                return '<option value="' + year + '">' + year + "</option>";
            }).join("");
            selectedYear = window.UGAYearFilter
                ? window.UGAYearFilter.selectedYear(years.map(function (year) { return { publication_date: year + "-01-01" }; }))
                : selectedYear;
            select.value = selectedYear;
            value.textContent = selectedYear;
            refreshControls();
        }

        trigger.addEventListener("click", function () {
            var isOpen = trigger.getAttribute("aria-expanded") === "true";
            trigger.setAttribute("aria-expanded", String(!isOpen));
            menu.hidden = isOpen;
            if (!isOpen) select.focus();
        });
        select.addEventListener("change", function () { applyYear(select.value); });
        stepButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                var nextIndex = years.indexOf(select.value) + Number(button.getAttribute("data-step"));
                if (years[nextIndex]) applyYear(years[nextIndex]);
            });
        });
        document.addEventListener("click", function (event) {
            if (!control.contains(event.target)) {
                menu.hidden = true;
                trigger.setAttribute("aria-expanded", "false");
            }
        });
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && !menu.hidden) {
                menu.hidden = true;
                trigger.setAttribute("aria-expanded", "false");
                trigger.focus();
            }
        });

        siteName.insertBefore(control, siteName.firstChild);
        value.textContent = selectedYear;
        select.innerHTML = '<option value="' + selectedYear + '">' + selectedYear + "</option>";
        refreshControls();

        var dataUrls = [
            new URL("graph_data.json", siteRootUrl),
            new URL("../graph_data.json", window.location.href),
            new URL("/graph_data.json", window.location.origin),
        ];
        dataUrls.reduce(function (promise, url) {
            return promise.catch(function () {
                return fetch(url).then(function (response) {
                    if (!response.ok) throw new Error("Graph data unavailable");
                    return response.json();
                });
            });
        }, Promise.reject(new Error("Graph data not loaded")))
            .then(function (data) {
                var papers = (data.nodes || []).filter(function (node) { return node.group === "paper"; });
                renderYears(window.UGAYearFilter ? window.UGAYearFilter.availableYears(papers) : []);
            })
            .catch(function () { });
    }

    document.addEventListener("DOMContentLoaded", function () {
        var preferredTheme = getPreferredTheme();
        applyTheme(preferredTheme);
        buildToggle();

        var logo = document.querySelector("#mkdocs-terminal-site-name a");
        if (logo) {
            logo.href = siteRootUrl.href;
            logo.textContent = "IAI@UGA Research is Awesome!";
        }

        var siteName = document.querySelector("#mkdocs-terminal-site-name");
        if (siteName) buildYearSelector(siteName);
    });

    var media = window.matchMedia("(prefers-color-scheme: dark)");
    if (typeof media.addEventListener === "function") {
        media.addEventListener("change", function () {
            if (!window.localStorage.getItem(STORAGE_KEY)) {
                applyTheme(getSystemTheme());
                var button = document.querySelector(".theme-toggle-btn");
                if (button) {
                    setButtonState(button, getSystemTheme());
                }
            }
        });
    }
})();
