(() => {
    const STORAGE_KEY = 'uga-selected-year';

    function yearFromPaper(paper) {
        return typeof paper?.publication_date === 'string'
            ? paper.publication_date.match(/^([0-9]{4})/)?.[1]
            : '';
    }

    function availableYears(papers) {
        return [...new Set(papers.map(yearFromPaper).filter(Boolean))]
            .sort((a, b) => Number(b) - Number(a));
    }

    function selectedYear(papers) {
        const years = availableYears(papers);
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved && years.includes(saved)) return saved;
        const current = String(new Date().getFullYear());
        return years.includes(current) ? current : (years[0] || current);
    }

    function setSelectedYear(year) {
        localStorage.setItem(STORAGE_KEY, String(year));
        const marker = document.querySelector('.header-year-marker');
        if (marker) marker.textContent = String(year);
        window.dispatchEvent(new CustomEvent('uga-year-change', { detail: { year: String(year) } }));
    }

    window.UGAYearFilter = {
        STORAGE_KEY,
        yearFromPaper,
        availableYears,
        selectedYear,
        setSelectedYear,
        paperMatchesSelectedYear: paper => {
            const year = localStorage.getItem(STORAGE_KEY) || String(new Date().getFullYear());
            return typeof paper?.publication_date === 'string' && paper.publication_date.startsWith(year);
        },
    };
})();
