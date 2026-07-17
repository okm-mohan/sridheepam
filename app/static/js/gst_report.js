document.addEventListener("DOMContentLoaded", function () {
    const page = document.querySelector(".gst-report-page");
    const shareButton = document.getElementById("gstSharePdf");
    const status = document.getElementById("gstShareStatus");

    if (!page || !shareButton) {
        return;
    }

    function showStatus(message, isError) {
        if (!status) {
            return;
        }
        status.textContent = message;
        status.classList.toggle("is-error", Boolean(isError));
        status.hidden = false;
        window.setTimeout(function () {
            status.hidden = true;
        }, 4500);
    }

    shareButton.addEventListener("click", async function () {
        const month = document.getElementById("gstMonth").value;
        const year = document.getElementById("gstYear").value;
        const reportType = page.dataset.reportType || "purchase";
        const pdfUrl = `${page.dataset.pdfUrl}?month=${encodeURIComponent(month)}&year=${encodeURIComponent(year)}&download=1`;
        const fileName = `${reportType}-gst-report-${year}-${String(month).padStart(2, "0")}.pdf`;

        shareButton.disabled = true;
        shareButton.classList.add("is-loading");

        try {
            const response = await fetch(pdfUrl, { credentials: "same-origin" });
            if (!response.ok) {
                throw new Error("Unable to prepare the PDF.");
            }

            const file = new File([await response.blob()], fileName, { type: "application/pdf" });
            if (navigator.share && (!navigator.canShare || navigator.canShare({ files: [file] }))) {
                await navigator.share({
                    title: `${reportType === "sales" ? "Sales" : "Purchase"} GST Report`,
                    text: `GST report for ${month}/${year}`,
                    files: [file]
                });
                showStatus("PDF shared successfully.");
            } else {
                const link = document.createElement("a");
                link.href = URL.createObjectURL(file);
                link.download = fileName;
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.setTimeout(function () { URL.revokeObjectURL(link.href); }, 1000);
                showStatus("Sharing is not supported by this browser, so the PDF was downloaded.");
            }
        } catch (error) {
            if (error && error.name === "AbortError") {
                showStatus("PDF sharing was cancelled.");
            } else {
                showStatus(error.message || "Unable to share the PDF.", true);
            }
        } finally {
            shareButton.disabled = false;
            shareButton.classList.remove("is-loading");
        }
    });
});
