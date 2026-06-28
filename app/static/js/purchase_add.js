// =========================================
// PURCHASE ADD
// =========================================

document.addEventListener("DOMContentLoaded", function () {
    addRow();
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
                    value="0"
                    step="0.001"
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
                    X
                </button>
            </td>

        </tr>
    `;

    tbody.insertAdjacentHTML("beforeend", row);
}

// =========================================
// REMOVE ROW
// =========================================

function removeRow(btn){

    btn.closest("tr").remove();

    calculateTotals();
}

// =========================================
// CALCULATE ROW
// =========================================

function calculateRow(input){

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

    calculateTotals();
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
        "₹ " + subTotal.toFixed(2);

    document.getElementById("gstTotal").innerHTML =
        "₹ " + gstTotal.toFixed(2);

    document.getElementById("grandTotal").innerHTML =
        "₹ " + grandTotal.toFixed(2);
}