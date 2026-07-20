// ======================================
// SALES ADD
// ======================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const rows = document.querySelectorAll("#salesBody tr");

        if (rows.length === 0) {
            addRow();
        } else {
            rows.forEach((row) => calculateRow(row.querySelector('[name="qty"]'), false));
            calculateTotals();
        }

        updateItemCount();

        const customerSearch = document.getElementById("customerSearch");
        if (customerSearch) {
            initializeCustomerCombobox();
            updateTaxMode();
        }

    }
);

function selectCustomerOption(option) {
    const search = document.getElementById("customerSearch");
    const customerId = document.getElementById("customerId");
    const optionsPanel = document.getElementById("customerOptions");
    const clearButton = document.getElementById("customerClear");
    if (!search || !customerId || !option) return;
    search.value = option.dataset.name;
    search.dataset.selectedName = option.dataset.name;
    customerId.value = option.dataset.id;
    customerId.dataset.gst = option.dataset.gst || "";
    customerId.dataset.state = option.dataset.state || "";
    search.setCustomValidity("");
    if (clearButton) clearButton.hidden = false;
    optionsPanel.hidden = true;
    search.setAttribute("aria-expanded", "false");
    recalculateAllRows();
}

function initializeCustomerCombobox() {
    const search = document.getElementById("customerSearch");
    const customerId = document.getElementById("customerId");
    const optionsPanel = document.getElementById("customerOptions");
    const clearButton = document.getElementById("customerClear");
    const options = Array.from(optionsPanel.querySelectorAll(".customer-option"));
    const noResults = optionsPanel.querySelector(".customer-no-results");
    let activeIndex = -1;
    const visibleOptions = () => options.filter((option) => !option.hidden);
    const openOptions = () => { optionsPanel.hidden = false; search.setAttribute("aria-expanded", "true"); };
    const setActive = (index) => {
        const visible = visibleOptions();
        options.forEach((option) => option.classList.remove("active"));
        if (!visible.length) { activeIndex = -1; return; }
        activeIndex = (index + visible.length) % visible.length;
        visible[activeIndex].classList.add("active");
        visible[activeIndex].scrollIntoView({ block: "nearest" });
    };
    const filterOptions = () => {
        const query = search.value.trim().toLowerCase();
        if (search.value !== (search.dataset.selectedName || "")) {
            customerId.value = "";
            customerId.dataset.gst = "";
            customerId.dataset.state = "";
            delete search.dataset.selectedName;
        }
        if (clearButton) clearButton.hidden = !search.value;
        options.forEach((option) => { option.hidden = !option.dataset.name.toLowerCase().includes(query); });
        noResults.hidden = visibleOptions().length > 0;
        activeIndex = -1;
        search.setCustomValidity(search.value && !customerId.value ? "Select a company from the dropdown." : "");
        openOptions();
        updateTaxMode();
    };
    search.addEventListener("focus", filterOptions);
    search.addEventListener("input", filterOptions);
    search.addEventListener("keydown", (event) => {
        if (event.key === "ArrowDown" || event.key === "ArrowUp") {
            event.preventDefault();
            openOptions();
            const visible = visibleOptions();
            const nextIndex = activeIndex < 0 ? (event.key === "ArrowDown" ? 0 : visible.length - 1) : activeIndex + (event.key === "ArrowDown" ? 1 : -1);
            setActive(nextIndex);
        } else if (event.key === "Enter" && (activeIndex >= 0 || visibleOptions().length === 1)) {
            event.preventDefault();
            selectCustomerOption(visibleOptions()[activeIndex >= 0 ? activeIndex : 0]);
        } else if (event.key === "Escape") {
            optionsPanel.hidden = true;
            search.setAttribute("aria-expanded", "false");
        }
    });
    options.forEach((option) => option.addEventListener("mousedown", (event) => { event.preventDefault(); selectCustomerOption(option); }));
    if (clearButton) clearButton.addEventListener("click", () => {
        search.value = "";
        delete search.dataset.selectedName;
        customerId.value = "";
        customerId.dataset.gst = "";
        customerId.dataset.state = "";
        search.setCustomValidity("");
        clearButton.hidden = true;
        options.forEach((option) => { option.hidden = false; option.classList.remove("active"); });
        noResults.hidden = true;
        openOptions();
        recalculateAllRows();
        search.focus();
    });
    search.addEventListener("blur", () => window.setTimeout(() => { optionsPanel.hidden = true; search.setAttribute("aria-expanded", "false"); }, 120));
}

function getTaxMode() {
    const form = document.querySelector(".sales-entry-form");
    const customer = form && form.querySelector('[name="customer_id"]');
    if (!form || !customer || !customer.value) return { known: false, intra: true, state: "" };
    const companyGst = (form.dataset.companyGst || "").trim();
    const partyGst = (customer.dataset.gst || "").trim();
    const companyCode = /^\d{2}/.test(companyGst) ? companyGst.slice(0, 2) : "";
    const partyCode = /^\d{2}/.test(partyGst) ? partyGst.slice(0, 2) : "";
    const normalizeState = (value) => String(value || "").toLowerCase().replace(/[^a-z0-9]/g, "");
    const companyState = normalizeState(form.dataset.companyState);
    const partyState = normalizeState(customer.dataset.state);
    const intra = companyState && partyState
        ? companyState === partyState
        : Boolean(companyCode && partyCode && companyCode === partyCode);
    return { known: true, intra, state: customer.dataset.state || "" };
}

function updateTaxMode() {
    const mode = getTaxMode();
    const banner = document.querySelector("[data-tax-mode]");
    if (!banner) return mode;
    banner.classList.toggle("inter-state", mode.known && !mode.intra);
    banner.querySelector("span").textContent = !mode.known
        ? "Select a customer to determine CGST/SGST or IGST."
        : mode.intra
            ? `Intra-State supply${mode.state ? ` (${mode.state})` : ""}: CGST + SGST applies.`
            : `Inter-State supply${mode.state ? ` (${mode.state})` : ""}: IGST applies.`;
    return mode;
}

function recalculateAllRows() {
    updateTaxMode();
    document.querySelectorAll("#salesBody tr").forEach((row) => calculateRow(row.querySelector('[name="qty"]'), false));
    calculateTotals();
}

// ======================================
// ADD ROW
// ======================================

function addRow() {

    let tbody =
        document.getElementById(
            "salesBody"
        );

    let row = `
<tr>

    <td>
        <select
            name="product_id"
            required
            onchange="productChanged(this)"
            class="form-control"
        >
            <option value="">Select Product</option>
            ${productsOptions}
        </select>
    </td>

    <td>
        <input
            type="number"
            name="qty"
            value="1"
            step="1"
            min="1"
            required
            onkeyup="calculateRow(this)"
            onchange="calculateRow(this)"
        >
    </td>

    <td>
        <input
            type="number"
            name="rate"
            value="0"
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

    <td><input type="number" name="cgst_amount" value="0" readonly></td>
    <td><input type="number" name="sgst_amount" value="0" readonly></td>
    <td><input type="number" name="igst_amount" value="0" readonly><input type="hidden" name="gst_amount" value="0"></td>

    <td>
        <input type="hidden" name="line_total" value="0">
        <input
            type="number"
            name="line_amount"
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

    tbody.insertAdjacentHTML(
        "beforeend",
        row
    );

    updateItemCount();
}

// ======================================
// PRODUCT CHANGED
// ======================================

function productChanged(select){

    let option =
        select.options[
            select.selectedIndex
        ];

    let row =
        select.closest("tr");

    const quantityInput = row.querySelector('[name="qty"]');
    if (!(Number(quantityInput.value) > 0)) quantityInput.value = "1";

    row.querySelector(
        '[name="rate"]'
    ).value =
        Number(option.dataset.rate || 0).toFixed(2);

    row.querySelector(
        '[name="gst_percent"]'
    ).value =
        Number(option.dataset.gst || 0).toFixed(2);

    calculateRow(select);
}

// ======================================
// REMOVE ROW
// ======================================

function removeRow(btn){

    btn.closest("tr").remove();

    if (document.querySelectorAll("#salesBody tr").length === 0) {
        addRow();
    }

    calculateTotals();
    updateItemCount();
}

// ======================================
// CALCULATE ROW
// ======================================

function calculateRow(input, updateTotals = true){

    if (!input) return;

    let row =
        input.closest("tr");

    let qty =
        parseFloat(
            row.querySelector(
                '[name="qty"]'
            ).value
        ) || 0;

    let rate =
        parseFloat(
            row.querySelector(
                '[name="rate"]'
            ).value
        ) || 0;

    let gstPercent =
        parseFloat(
            row.querySelector(
                '[name="gst_percent"]'
            ).value
        ) || 0;

    let amount =
        qty * rate;

    let gstAmount =
        amount * gstPercent / 100;

    const taxMode = getTaxMode();
    const cgstAmount = taxMode.intra ? Number((gstAmount / 2).toFixed(2)) : 0;
    const sgstAmount = taxMode.intra ? Number((gstAmount - cgstAmount).toFixed(2)) : 0;
    const igstAmount = taxMode.intra ? 0 : Number(gstAmount.toFixed(2));

    let lineTotal =
        amount + gstAmount;

    row.querySelector(
        '[name="gst_amount"]'
    ).value =
        gstAmount.toFixed(2);

    row.querySelector('[name="cgst_amount"]').value = cgstAmount.toFixed(2);
    row.querySelector('[name="sgst_amount"]').value = sgstAmount.toFixed(2);
    row.querySelector('[name="igst_amount"]').value = igstAmount.toFixed(2);

    row.querySelector(
        '[name="line_total"]'
    ).value =
        lineTotal.toFixed(2);

    row.querySelector('[name="line_amount"]').value = amount.toFixed(2);

    if (updateTotals) calculateTotals();
}

// ======================================
// CALCULATE TOTALS
// ======================================

function calculateTotals(){

    let subTotal = 0;
    let gstTotal = 0;
    let cgstTotal = 0;
    let sgstTotal = 0;
    let igstTotal = 0;
    let grandTotal = 0;

    document
    .querySelectorAll(
        '[name="qty"]'
    )
    .forEach(function(field){

        let row =
            field.closest("tr");

        let qty =
            parseFloat(
                row.querySelector(
                    '[name="qty"]'
                ).value
            ) || 0;

        let rate =
            parseFloat(
                row.querySelector(
                    '[name="rate"]'
                ).value
            ) || 0;

        let gst =
            parseFloat(
                row.querySelector(
                    '[name="gst_amount"]'
                ).value
            ) || 0;

        let total =
            parseFloat(
                row.querySelector(
                    '[name="line_total"]'
                ).value
            ) || 0;

        subTotal += qty * rate;
        gstTotal += gst;
        cgstTotal += parseFloat(row.querySelector('[name="cgst_amount"]').value) || 0;
        sgstTotal += parseFloat(row.querySelector('[name="sgst_amount"]').value) || 0;
        igstTotal += parseFloat(row.querySelector('[name="igst_amount"]').value) || 0;
        grandTotal += total;

    });

    document.getElementById(
        "subTotal"
    ).innerHTML =
        "\u20B9 " +
        subTotal.toFixed(2);

    document.getElementById(
        "gstTotal"
    ).innerHTML =
        "\u20B9 " +
        gstTotal.toFixed(2);

    document.getElementById("cgstTotal").innerHTML = "\u20B9 " + cgstTotal.toFixed(2);
    document.getElementById("sgstTotal").innerHTML = "\u20B9 " + sgstTotal.toFixed(2);
    document.getElementById("igstTotal").innerHTML = "\u20B9 " + igstTotal.toFixed(2);

    document.getElementById(
        "grandTotal"
    ).innerHTML =
        "\u20B9 " +
        grandTotal.toFixed(2);
}

function updateItemCount() {
    const count = document.querySelectorAll("#salesBody tr").length;
    const label = document.getElementById("itemCount");

    if (label) {
        label.textContent = `${count} item${count === 1 ? "" : "s"}`;
    }
}


