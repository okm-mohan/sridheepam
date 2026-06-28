// =============================
// Sridheepam ERP Login
// =============================

// Show / Hide Password
function togglePassword() {

    const password = document.getElementById("password");
    const eye = document.getElementById("eyeIcon");

    if (password.type === "password") {
        password.type = "text";
        eye.classList.remove("fa-eye");
        eye.classList.add("fa-eye-slash");
    } else {
        password.type = "password";
        eye.classList.remove("fa-eye-slash");
        eye.classList.add("fa-eye");
    }

}


// Form Validation
document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("loginForm");

    form.addEventListener("submit", function (e) {

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        if (username === "") {
            e.preventDefault();
            alert("Please enter Username.");
            document.getElementById("username").focus();
            return;
        }

        if (password === "") {
            e.preventDefault();
            alert("Please enter Password.");
            document.getElementById("password").focus();
            return;
        }

        // Show loading state
        const btn = document.querySelector(".login-btn");

        btn.disabled = true;
        btn.innerHTML =
            '<i class="fa-solid fa-spinner fa-spin"></i> Signing In...';

    });

});


// Press Enter to Login
document.addEventListener("keypress", function (e) {

    if (e.key === "Enter") {
        document.getElementById("loginForm").requestSubmit();
    }

});


// Auto Focus Username
window.onload = function () {

    document.getElementById("username").focus();

};