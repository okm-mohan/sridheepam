document.addEventListener("DOMContentLoaded", function () {

    // ============================
    // Input Focus Animation
    // ============================

    const inputs = document.querySelectorAll(".input-box input, .input-box textarea");

    inputs.forEach(input => {

        input.addEventListener("focus", function () {
            this.parentElement.classList.add("active");
        });

        input.addEventListener("blur", function () {

            this.parentElement.classList.remove("active");

        });

    });


    // ============================
    // Save Button Loading Effect
    // ============================

    const form = document.querySelector(".company-card");

    form.addEventListener("submit", function (e) {

        e.preventDefault();

        const btn = document.querySelector(".save-btn");

        btn.disabled = true;

        btn.innerHTML = `
            <i class="fa-solid fa-spinner fa-spin"></i>
            Saving...
        `;

        setTimeout(function () {

            btn.innerHTML = `
                <i class="fa-solid fa-circle-check"></i>
                Saved Successfully
            `;

            btn.style.background = "#16a34a";

            setTimeout(function () {

                btn.innerHTML = `
                    <i class="fa-solid fa-floppy-disk"></i>
                    Save Company
                `;

                btn.style.background = "";

                btn.disabled = false;

            }, 2000);

        }, 1500);

    });

});