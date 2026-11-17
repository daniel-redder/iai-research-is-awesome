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
    }

    document.addEventListener("DOMContentLoaded", function () {
        applyTheme(getPreferredTheme());
        buildToggle();
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
