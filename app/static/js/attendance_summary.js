document.addEventListener("DOMContentLoaded", () => {
    const preview = document.querySelector(".report-preview");
    if (!preview) return;

    const pageCount = Number(preview.dataset.pageCount || 1);
    const currentPageLabel = document.querySelector("[data-current-page]");
    let currentPage = 1;

    const showPage = (pageNumber) => {
        currentPage = Math.min(pageCount, Math.max(1, pageNumber));
        document.querySelectorAll("[data-report-page]").forEach((page) => {
            page.classList.toggle("screen-hidden", Number(page.dataset.reportPage) !== currentPage);
        });
        if (currentPageLabel) currentPageLabel.textContent = String(currentPage);
    };

    document.querySelectorAll("[data-page-action]").forEach((button) => {
        button.addEventListener("click", () => {
            showPage(currentPage + (button.dataset.pageAction === "next" ? 1 : -1));
        });
    });

    const printButton = document.querySelector("[data-print-report]");
    if (printButton) printButton.addEventListener("click", () => window.print());
});
