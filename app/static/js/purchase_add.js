// =========================================
// PURCHASE ADD
// =========================================

document.addEventListener("DOMContentLoaded", function () {
    const rows = document.querySelectorAll("#purchaseBody tr");

    if (rows.length === 0) {
        addRow();
    } else {
        rows.forEach((row) => calculateRow(row.querySelector('[name="qty"]'), false));
        calculateTotals();
        updateItemCount();
    }
});

// =========================================
// ADD ROW
// =========================================

function addRow() {

    let tbody = document.getElementById("purchaseBody");

    let row = `
        <tr>

            <td>
                <select name="material_id" required>
                    <option value="">Select Material</option>
                    ${materialsOptions}
                </select>
            </td>

            <td>
                <input
                    type="number"
                    name="qty"
                    value=""
                    placeholder="0.000"
                    step="0.001"
                    min="0.001"
                    required
                    onkeyup="calculateRow(this)"
                    onchange="calculateRow(this)"
                >
            </td>

            <td>
                <input
                    type="number"
                    name="rate"
                    value=""
                    placeholder="0.00"
                    step="0.01"
                    min="0"
                    required
                    onkeyup="calculateRow(this)"
                    onchange="calculateRow(this)"
                >
            </td>

            <td>
                <input
                    type="number"
                    name="gst_percent"
                    value="0"
                    step="0.01"
                    min="0"
                    onkeyup="calculateRow(this)"
                    onchange="calculateRow(this)"
                >
            </td>

            <td>
                <input
                    type="number"
                    name="gst_amount"
                    value="0"
                    readonly
                >
            </td>

            <td>
                <input
                    type="number"
                    name="line_total"
                    value="0"
                    readonly
                >
            </td>

            <td>
                <button
                    type="button"
                    class="btn-remove"
                    onclick="removeRow(this)"
                >
                    <i class="bi bi-trash3"></i>
                    <span class="visually-hidden">Remove item</span>
                </button>
            </td>

        </tr>
    `;

    tbody.insertAdjacentHTML("beforeend", row);
    updateItemCount();
}

// =========================================
// REMOVE ROW
// =========================================

function removeRow(btn){

    btn.closest("tr").remove();

    if (document.querySelectorAll("#purchaseBody tr").length === 0) {
        addRow();
    }

    calculateTotals();
    updateItemCount();
}

// =========================================
// CALCULATE ROW
// =========================================

function calculateRow(input, updateTotals = true){

    if (!input) return;

    let row = input.closest("tr");

    let qty =
        parseFloat(
            row.querySelector('[name="qty"]').value
        ) || 0;

    let rate =
        parseFloat(
            row.querySelector('[name="rate"]').value
        ) || 0;

    let gstPercent =
        parseFloat(
            row.querySelector('[name="gst_percent"]').value
        ) || 0;

    let amount = qty * rate;

    let gstAmount =
        amount * gstPercent / 100;

    let lineTotal =
        amount + gstAmount;

    row.querySelector(
        '[name="gst_amount"]'
    ).value = gstAmount.toFixed(2);

    row.querySelector(
        '[name="line_total"]'
    ).value = lineTotal.toFixed(2);

    if (updateTotals) calculateTotals();
}

// =========================================
// CALCULATE TOTALS
// =========================================

function calculateTotals(){

    let subTotal = 0;
    let gstTotal = 0;
    let grandTotal = 0;

    document
        .querySelectorAll('[name="qty"]')
        .forEach((qtyField)=>{

            let row = qtyField.closest("tr");

            let qty =
                parseFloat(
                    row.querySelector('[name="qty"]').value
                ) || 0;

            let rate =
                parseFloat(
                    row.querySelector('[name="rate"]').value
                ) || 0;

            let gst =
                parseFloat(
                    row.querySelector('[name="gst_amount"]').value
                ) || 0;

            let total =
                parseFloat(
                    row.querySelector('[name="line_total"]').value
                ) || 0;

            subTotal += qty * rate;
            gstTotal += gst;
            grandTotal += total;
        });

    document.getElementById("subTotal").innerHTML =
        "\u20B9 " + subTotal.toFixed(2);

    document.getElementById("gstTotal").innerHTML =
        "\u20B9 " + gstTotal.toFixed(2);

    document.getElementById("grandTotal").innerHTML =
        "\u20B9 " + grandTotal.toFixed(2);
}

function updateItemCount() {
    const count = document.querySelectorAll("#purchaseBody tr").length;
    const label = document.getElementById("itemCount");

    if (label) {
        label.textContent = `${count} item${count === 1 ? "" : "s"}`;
    }
}

// =========================================
// AI INVOICE OCR CAPTURE
// =========================================

document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("purchaseEntryForm");
    const uploadInput = document.getElementById("invoiceImageUpload");
    const cameraInput = document.getElementById("invoiceImageCamera");
    if (!form || !uploadInput || !cameraInput) return;

    const workspace = document.getElementById("invoiceOcrWorkspace");
    const preview = document.getElementById("invoicePreview");
    const previewPlaceholder = document.getElementById("invoicePreviewPlaceholder");
    const statusTitle = document.getElementById("ocrStatusTitle");
    const statusText = document.getElementById("ocrStatusText");
    const statusIcon = document.getElementById("ocrStatusIcon");
    const progressValue = document.getElementById("ocrProgressValue");
    const progressBar = document.getElementById("ocrProgressBar");
    const resultChecks = document.getElementById("ocrResultChecks");
    const reviewActions = document.getElementById("ocrReviewActions");
    const reviewButton = document.getElementById("ocrReviewButton");
    const saveButton = document.getElementById("ocrSaveButton");
    const autoSave = document.getElementById("ocrAutoSave");
    const ocrTextField = document.getElementById("ocrText");
    const confidenceField = document.getElementById("ocrConfidence");
    const entrySourceField = document.getElementById("entrySource");
    let extractionReady = false;

    const normalizeText = (value) => String(value || "")
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, " ")
        .trim();

    const setProgress = (percent, title, detail) => {
        const safePercent = Math.max(0, Math.min(100, Math.round(percent)));
        progressValue.textContent = `${safePercent}%`;
        progressBar.style.width = `${safePercent}%`;
        if (title) statusTitle.textContent = title;
        if (detail) statusText.textContent = detail;
    };

    const setWorkspaceState = (state, icon, title, detail) => {
        workspace.classList.remove("ocr-success", "ocr-warning", "ocr-error");
        if (state) workspace.classList.add(state);
        statusIcon.innerHTML = `<i class="bi ${icon}"></i>`;
        statusTitle.textContent = title;
        statusText.textContent = detail;
    };

    const setCheck = (name, matched) => {
        const item = resultChecks.querySelector(`[data-check="${name}"]`);
        if (!item) return;
        item.classList.remove("matched", "missing");
        item.classList.add(matched ? "matched" : "missing");
        item.querySelector("i").className = `bi ${matched ? "bi-check-circle-fill" : "bi-exclamation-circle-fill"}`;
    };

    const parseDate = (text) => {
        const labelled = text.match(/(?:invoice\s*date|bill\s*date|dated|date)\s*[:#-]?\s*(\d{1,4}[\/.\-]\d{1,2}[\/.\-]\d{1,4})/i);
        const general = text.match(/\b(\d{1,4}[\/.\-]\d{1,2}[\/.\-]\d{1,4})\b/);
        const value = (labelled || general || [])[1];
        if (!value) return "";

        const parts = value.split(/[\/.\-]/).map(Number);
        let year;
        let month;
        let day;
        if (String(parts[0]).length === 4) {
            [year, month, day] = parts;
        } else {
            [day, month, year] = parts;
            if (year < 100) year += 2000;
        }
        const parsed = new Date(year, month - 1, day);
        if (parsed.getFullYear() !== year || parsed.getMonth() !== month - 1 || parsed.getDate() !== day) return "";
        return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    };

    const findInvoiceNumber = (text) => {
        const patterns = [
            /(?:tax\s*)?invoice\s*(?:no|number|#)\s*[:#-]?\s*([a-z0-9][a-z0-9\/-]{2,})/i,
            /(?:bill|inv)\s*(?:no|number|#)\s*[:#-]?\s*([a-z0-9][a-z0-9\/-]{2,})/i
        ];
        for (const pattern of patterns) {
            const match = text.match(pattern);
            if (match && !/^(date|dated)$/i.test(match[1])) return match[1].toUpperCase();
        }
        return "";
    };

    const matchSupplier = (text) => {
        const normalizedInvoice = normalizeText(text);
        const supplierSelect = form.querySelector('[name="supplier_id"]');
        let bestMatch = null;
        supplierSelect.querySelectorAll("option[data-name]").forEach((option) => {
            const normalizedName = normalizeText(option.dataset.name);
            if (normalizedName.length >= 3 && normalizedInvoice.includes(normalizedName)) {
                if (!bestMatch || normalizedName.length > bestMatch.nameLength) {
                    bestMatch = { value: option.value, nameLength: normalizedName.length };
                }
            }
        });
        if (bestMatch) supplierSelect.value = bestMatch.value;
        return Boolean(bestMatch);
    };

    const getMaterialCatalog = () => {
        const sampleSelect = form.querySelector('[name="material_id"]');
        if (!sampleSelect) return [];
        return Array.from(sampleSelect.querySelectorAll("option[data-name]")).map((option) => ({
            id: option.value,
            name: option.dataset.name,
            normalizedName: normalizeText(option.dataset.name),
            gst: Number(option.dataset.gst || 0),
            price: Number(option.dataset.price || 0)
        }));
    };

    const matchMaterials = (text) => {
        const lines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
        const catalog = getMaterialCatalog();
        const matches = [];

        catalog.forEach((material) => {
            const nameTokens = material.normalizedName.split(" ").filter((token) => token.length > 1);
            let lineIndex = -1;
            lines.some((line, index) => {
                const normalizedLine = normalizeText(line);
                const tokenMatches = nameTokens.filter((token) => normalizedLine.includes(token)).length;
                if (normalizedLine.includes(material.normalizedName) || (nameTokens.length && tokenMatches / nameTokens.length >= 0.7)) {
                    lineIndex = index;
                    return true;
                }
                return false;
            });
            if (lineIndex < 0) return;

            let numericSource = `${lines[lineIndex]} ${lines[lineIndex + 1] || ""}`;
            const namePosition = numericSource.toLowerCase().indexOf(material.name.toLowerCase());
            if (namePosition >= 0) numericSource = numericSource.slice(namePosition + material.name.length);
            let numbers = (numericSource.match(/\d[\d,]*(?:\.\d+)?/g) || [])
                .map((value) => Number(value.replace(/,/g, "")))
                .filter((value) => Number.isFinite(value));

            if (numbers.length >= 4 && Number.isInteger(numbers[0]) && numbers[0] >= 1000) numbers.shift();
            if (numbers.length >= 3) numbers.pop();
            const gstIndex = numbers.findIndex((value, index) => index > 0 && Math.abs(value - material.gst) < 0.01);
            if (gstIndex > 1) numbers.splice(gstIndex, 1);

            const quantity = numbers[0] > 0 ? numbers[0] : 0;
            const rate = numbers[1] > 0 ? numbers[1] : material.price;
            if (quantity > 0 && rate > 0) {
                matches.push({ id: material.id, quantity, rate, gst: material.gst });
            }
        });
        return matches;
    };

    const fillMaterialRows = (items) => {
        if (!items.length) return;
        const body = document.getElementById("purchaseBody");
        body.innerHTML = "";
        items.forEach((item) => {
            addRow();
            const rows = body.querySelectorAll("tr");
            const row = rows[rows.length - 1];
            row.querySelector('[name="material_id"]').value = item.id;
            row.querySelector('[name="qty"]').value = item.quantity;
            row.querySelector('[name="rate"]').value = item.rate.toFixed(2);
            row.querySelector('[name="gst_percent"]').value = item.gst.toFixed(2);
            calculateRow(row.querySelector('[name="qty"]'), false);
        });
        calculateTotals();
        updateItemCount();
    };

    const applyOcrResult = (text, confidence) => {
        const supplierMatched = matchSupplier(text);
        const invoiceNumber = findInvoiceNumber(text);
        const invoiceDate = parseDate(text);
        const materialMatches = matchMaterials(text);

        if (invoiceNumber) form.querySelector('[name="invoice_no"]').value = invoiceNumber;
        if (invoiceDate) form.querySelector('[name="invoice_date"]').value = invoiceDate;
        fillMaterialRows(materialMatches);

        ocrTextField.value = text;
        confidenceField.value = Number(confidence || 0).toFixed(2);
        entrySourceField.value = "OCR";
        resultChecks.hidden = false;
        setCheck("supplier", supplierMatched);
        setCheck("invoice", Boolean(invoiceNumber));
        setCheck("date", Boolean(invoiceDate));
        setCheck("items", materialMatches.length > 0);

        extractionReady = supplierMatched && materialMatches.length > 0;
        reviewActions.hidden = false;
        saveButton.disabled = !extractionReady;

        if (extractionReady) {
            setProgress(100, "Invoice fields filled", `${materialMatches.length} material${materialMatches.length === 1 ? "" : "s"} matched with ${Math.round(confidence || 0)}% OCR confidence.`);
            setWorkspaceState("ocr-success", "bi-check-circle-fill", "Invoice fields filled", autoSave.checked ? "Verified master records found. Saving purchase automatically..." : "Review the filled entry or save the OCR purchase.");
            if (autoSave.checked) {
                window.setTimeout(() => {
                    if (form.checkValidity()) form.requestSubmit();
                    else {
                        form.reportValidity();
                        setWorkspaceState("ocr-warning", "bi-exclamation-triangle-fill", "Review required", "Some required fields need your confirmation before saving.");
                    }
                }, 900);
            }
        } else {
            setProgress(100, "Review required", "OCR filled the fields it could recognize, but required master records were not confidently matched.");
            setWorkspaceState("ocr-warning", "bi-exclamation-triangle-fill", "Review required", "Select the missing supplier or material details, then save the purchase manually.");
        }
    };

    const processInvoice = async (file, sourceInput) => {
        if (!file) return;
        if (file.size > 10 * 1024 * 1024) {
            workspace.hidden = false;
            setWorkspaceState("ocr-error", "bi-x-circle-fill", "Image is too large", "Choose an invoice image smaller than 10 MB.");
            return;
        }

        if (sourceInput === uploadInput) cameraInput.value = "";
        if (sourceInput === cameraInput) uploadInput.value = "";
        workspace.hidden = false;
        workspace.classList.remove("ocr-success", "ocr-warning", "ocr-error");
        resultChecks.hidden = true;
        reviewActions.hidden = true;
        extractionReady = false;
        setProgress(2, "Preparing invoice", "Loading the selected image...");
        preview.src = URL.createObjectURL(file);
        preview.hidden = false;
        previewPlaceholder.hidden = true;

        if (!window.Tesseract) {
            setWorkspaceState("ocr-error", "bi-wifi-off", "OCR service unavailable", "The OCR library could not load. Check the internet connection and try again.");
            return;
        }

        try {
            const result = await window.Tesseract.recognize(file, "eng", {
                logger(message) {
                    if (message.status === "recognizing text") {
                        setProgress(15 + (message.progress || 0) * 75, "Reading invoice", "Recognizing supplier, invoice details and material lines...");
                    } else if (message.status) {
                        setProgress(Math.max(5, Number(progressValue.textContent.replace("%", "")) || 5), "Preparing OCR", message.status.replace(/\b\w/g, (letter) => letter.toUpperCase()));
                    }
                }
            });
            applyOcrResult(result.data.text || "", result.data.confidence || 0);
        } catch (error) {
            setWorkspaceState("ocr-error", "bi-x-circle-fill", "Could not read invoice", "Use a clear, straight image with good lighting and try again.");
            statusText.title = error.message || "OCR error";
        }
    };

    uploadInput.addEventListener("change", () => processInvoice(uploadInput.files[0], uploadInput));
    cameraInput.addEventListener("change", () => processInvoice(cameraInput.files[0], cameraInput));

    reviewButton.addEventListener("click", () => {
        form.querySelector('[name="supplier_id"]').scrollIntoView({ behavior: "smooth", block: "center" });
    });

    saveButton.addEventListener("click", () => {
        if (!extractionReady) return;
        if (form.checkValidity()) form.requestSubmit();
        else form.reportValidity();
    });
});
