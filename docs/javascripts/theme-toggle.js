(function () {
    var STORAGE_KEY = "uga-theme";

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
            githubLink.innerHTML = '<svg viewBox="0 0 16 16" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82A7.65 7.65 0 0 1 8 4.58c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/></svg>';

            githubItem.appendChild(githubLink);
            menu.appendChild(githubItem);
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        var preferredTheme = getPreferredTheme();
        applyTheme(preferredTheme);
        buildToggle();

        var logo = document.querySelector("#mkdocs-terminal-site-name a");
        if (logo) {
            logo.innerHTML = "IAI@UGA<br>Research is<br>Awesome!";
        }
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
