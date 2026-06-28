//========================================================
// Purchase Report
//========================================================

let purchaseData = [];

let filteredData = [];

let currentPage = 1;

let pageSize = 25;

let sortColumn = "purchase_date";

let sortDirection = "asc";


//========================================================
// Page Load
//========================================================

document.addEventListener("DOMContentLoaded", function () {

    initializePurchaseReport();

});


//========================================================

function initializePurchaseReport() {

    document
        .getElementById("btnSearch")
        .addEventListener("click", loadPurchaseReport);


    document
        .getElementById("pageSize")
        .addEventListener("change", function () {

            pageSize = Number(this.value);

            currentPage = 1;

            renderTable();

        });


    document
        .getElementById("group_date")
        .addEventListener("change", function () {

            renderTable();

        });


    document
        .getElementById("btnPrint")
        .addEventListener("click", function () {

            window.print();

        });


    document
        .getElementById("btnExcel")
        .addEventListener("click", function () {

            alert("Excel Export will be connected later.");

        });


    document
        .getElementById("btnPdf")
        .addEventListener("click", function () {

            alert("PDF Export will be connected later.");

        });

}