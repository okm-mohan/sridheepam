document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-gst-master]").forEach(function (gstInput) {
        const form = gstInput.closest("form");
        if (!form) return;

        const cgstInput = form.querySelector('[data-gst-component="cgst"]');
        const sgstInput = form.querySelector('[data-gst-component="sgst"]');
        const igstInput = form.querySelector('[data-gst-component="igst"]');

        function updateComponents() {
            const gst = Math.max(Number(gstInput.value || 0), 0);
            const cgst = Number((gst / 2).toFixed(2));
            if (cgstInput) cgstInput.value = cgst.toFixed(2);
            if (sgstInput) sgstInput.value = (gst - cgst).toFixed(2);
            if (igstInput) igstInput.value = gst.toFixed(2);
        }

        gstInput.addEventListener("input", updateComponents);
        updateComponents();
    });
});
