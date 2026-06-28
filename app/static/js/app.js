document.addEventListener("DOMContentLoaded", function () {

    let current = window.location.pathname.toLowerCase();

    document.querySelectorAll(".menu-list a").forEach(function(link){

        let href = new URL(link.href).pathname.toLowerCase();

        // Dashboard
        if(current === "/dashboard" && href === "/dashboard"){
            link.classList.add("active");
        }

        // Other pages
        else if(current === href){
            link.classList.add("active");
        }

    });

});