document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("attendanceSheetForm");
    if (!form) return;

    const statusClasses = [
        "status-blank",
        "status-p",
        "status-a",
        "status-l",
        "status-hd",
        "status-wo",
        "status-h"
    ];

    const paintStatus = (select) => {
        select.classList.remove(...statusClasses);
        select.classList.add(`status-${select.value.toLowerCase() || "blank"}`);
    };

    const formatTotal = (value) => Number.isInteger(value) ? String(value) : value.toFixed(1);

    const updateRowTotals = (row) => {
        let present = 0;
        let leave = 0;
        let absent = 0;

        row.querySelectorAll(".daily-status").forEach((select) => {
            if (select.value === "P") present += 1;
            if (select.value === "HD") {
                present += 0.5;
                absent += 0.5;
            }
            if (["L", "WO", "H"].includes(select.value)) leave += 1;
            if (select.value === "A") absent += 1;
        });

        row.querySelector('[data-total="present"]').textContent = formatTotal(present);
        row.querySelector('[data-total="leave"]').textContent = formatTotal(leave);
        row.querySelector('[data-total="absent"]').textContent = formatTotal(absent);
    };

    const updateAllRows = () => {
        form.querySelectorAll("[data-employee-row]").forEach(updateRowTotals);
    };

    form.querySelectorAll(".daily-status").forEach((select) => {
        paintStatus(select);
        select.addEventListener("change", () => {
            paintStatus(select);
            updateRowTotals(select.closest("[data-employee-row]"));
        });
    });

    document.querySelectorAll("[data-fill]").forEach((button) => {
        button.addEventListener("click", () => {
            const action = button.dataset.fill;
            form.querySelectorAll(".daily-status").forEach((select) => {
                if (action === "clear") {
                    select.value = "";
                } else if (action === "current-day" && select.dataset.day === button.dataset.currentDay) {
                    select.value = "P";
                } else if (action === "working" && !select.value) {
                    select.value = select.dataset.weekend === "true" ? "WO" : "P";
                }
                paintStatus(select);
            });
            updateAllRows();
        });
    });

    const saveMessage = document.querySelector(".attendance-save-message");
    const dismissSaveMessage = document.querySelector("[data-dismiss-save-message]");
    if (saveMessage && dismissSaveMessage) {
        dismissSaveMessage.addEventListener("click", () => saveMessage.remove());
    }

    updateAllRows();
});
