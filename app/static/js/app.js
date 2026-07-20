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

    const sidebar = document.getElementById("sidebar");
    const menuToggle = document.getElementById("menuToggle");
    const backdrop = document.getElementById("sidebarBackdrop");
    const mobileBreakpoint = 991;

    // Each page load recreates the fixed sidebar at scroll position 0. Keep the
    // currently selected menu item visible without moving the main page.
    const activeMenuLink = sidebar && sidebar.querySelector(".menu-list a.active");
    if (sidebar && activeMenuLink) {
        requestAnimationFrame(function () {
            const linkTop = activeMenuLink.getBoundingClientRect().top - sidebar.getBoundingClientRect().top + sidebar.scrollTop;
            const targetTop = Math.max(0, linkTop - (sidebar.clientHeight - activeMenuLink.offsetHeight) / 2);
            sidebar.scrollTo({ top: targetTop, behavior: "auto" });
        });
    }

    function setSidebar(open) {
        if (!sidebar || !menuToggle || !backdrop) return;

        sidebar.classList.toggle("is-open", open);
        backdrop.classList.toggle("is-visible", open);
        document.body.classList.toggle("sidebar-open", open);
        menuToggle.setAttribute("aria-expanded", String(open));
        menuToggle.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");

        const icon = menuToggle.querySelector("i");
        if (icon) {
            icon.className = open ? "bi bi-x-lg" : "bi bi-list";
        }
    }

    if (menuToggle) {
        menuToggle.addEventListener("click", function () {
            setSidebar(!sidebar.classList.contains("is-open"));
        });
    }

    if (backdrop) {
        backdrop.addEventListener("click", function () {
            setSidebar(false);
        });
    }

    if (sidebar) {
        sidebar.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", function () {
                if (window.innerWidth <= mobileBreakpoint) setSidebar(false);
            });
        });
    }

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") setSidebar(false);
    });

    window.addEventListener("resize", function () {
        if (window.innerWidth > mobileBreakpoint) setSidebar(false);
    });

});
