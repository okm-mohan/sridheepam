document.addEventListener("DOMContentLoaded", function () {
    const printInvoice = function () { window.print(); };
    const printButton = document.querySelector("[data-print-preview]");
    const downloadButton = document.querySelector("[data-download-pdf]");
    const shareButton = document.querySelector("[data-share-invoice]");

    if (printButton) printButton.addEventListener("click", printInvoice);
    if (downloadButton) {
        downloadButton.addEventListener("click", function () {
            window.print();
        });
    }
    if (shareButton) {
        shareButton.addEventListener("click", async function () {
            const invoiceNumber = document.title.replace("GST Invoice - ", "");
            const payload = { title: "GST Invoice " + invoiceNumber, text: "GST Invoice " + invoiceNumber, url: window.location.href.replace(/[?&]print=1/, "") };
            try {
                if (navigator.share) await navigator.share(payload);
                else if (navigator.clipboard) {
                    await navigator.clipboard.writeText(payload.url);
                    shareButton.textContent = "Invoice Link Copied";
                    window.setTimeout(function () { shareButton.textContent = "Share Invoice"; }, 1800);
                }
            } catch (error) {
                if (error.name !== "AbortError") console.warn("Invoice sharing failed", error);
            }
        });
    }
    if (new URLSearchParams(window.location.search).get("print") === "1") window.setTimeout(printInvoice, 250);
});
