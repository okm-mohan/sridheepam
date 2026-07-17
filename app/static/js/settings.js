document.addEventListener("DOMContentLoaded", () => {
    const formatInput = document.getElementById("invoiceFormat");
    const digitsInput = document.getElementById("invoiceDigits");
    const nextInput = document.getElementById("invoiceNextNumber");
    const preview = document.getElementById("invoicePreview");
    const checkboxes = Array.from(document.querySelectorAll(".screen-checkbox"));

    function updatePreview() {
        const now = new Date();
        const digits = Math.max(1, Math.min(Number(digitsInput.value) || 6, 12));
        const sequence = Math.max(1, Number(nextInput.value) || 1);
        const number = String(sequence).padStart(digits, "0");
        preview.textContent = (formatInput.value || "SAL{NUMBER}")
            .replaceAll("{NUMBER}", number)
            .replaceAll("{YYYY}", String(now.getFullYear()))
            .replaceAll("{YY}", String(now.getFullYear()).slice(-2))
            .replaceAll("{MM}", String(now.getMonth() + 1).padStart(2, "0"));
    }

    [formatInput, digitsInput, nextInput].forEach((input) => input.addEventListener("input", updatePreview));
    document.getElementById("enableAll").addEventListener("click", () => checkboxes.forEach((item) => { item.checked = true; }));
    document.getElementById("disableAll").addEventListener("click", () => checkboxes.forEach((item) => { item.checked = false; }));
    updatePreview();
});
