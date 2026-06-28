// ======================================
// SALES ADD
// ======================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        addRow();

    }
);

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
            step="0.001"
            class="form-control"
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
            class="form-control"
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
            class="form-control"
            onkeyup="calculateRow(this)"
            onchange="calculateRow(this)"
        >
    </td>

    <td>
        <input
            type="number"
            name="gst_amount"
            value="0"
            class="form-control"
            readonly
        >
    </td>

    <td>
        <input
            type="number"
            name="line_total"
            value="0"
            class="form-control"
            readonly
        >
    </td>

    <td>
        <button
            type="button"
            class="btn-remove"
            onclick="removeRow(this)"
        >
            ✕
        </button>
    </td>

</tr>
`;

    tbody.insertAdjacentHTML(
        "beforeend",
        row
    );
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

    row.querySelector(
        '[name="rate"]'
    ).value =
        option.dataset.rate || 0;

    row.querySelector(
        '[name="gst_percent"]'
    ).value =
        option.dataset.gst || 0;

    calculateRow(select);
}

// ======================================
// REMOVE ROW
// ======================================

function removeRow(btn){

    btn.closest("tr").remove();

    calculateTotals();
}

// ======================================
// CALCULATE ROW
// ======================================

function calculateRow(input){

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

    let lineTotal =
        amount + gstAmount;

    row.querySelector(
        '[name="gst_amount"]'
    ).value =
        gstAmount.toFixed(2);

    row.querySelector(
        '[name="line_total"]'
    ).value =
        lineTotal.toFixed(2);

    calculateTotals();
}

// ======================================
// CALCULATE TOTALS
// ======================================

function calculateTotals(){

    let subTotal = 0;
    let gstTotal = 0;
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
        grandTotal += total;

    });

    document.getElementById(
        "subTotal"
    ).innerHTML =
        "₹ " +
        subTotal.toFixed(2);

    document.getElementById(
        "gstTotal"
    ).innerHTML =
        "₹ " +
        gstTotal.toFixed(2);

    document.getElementById(
        "grandTotal"
    ).innerHTML =
        "₹ " +
        grandTotal.toFixed(2);
}


