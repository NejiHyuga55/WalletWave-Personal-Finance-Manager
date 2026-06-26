// Smooth Scrolling for internal links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute("href"));
        if (target) {
            target.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        }
    });
});

// Dropdown Menu Functionality
document.querySelectorAll('.nav-links li a').forEach(link => {
    link.addEventListener('click', function() {
        const submenu = this.nextElementSibling;
        if (submenu) {
            submenu.classList.toggle('show');
        }
    });
});

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    const isClickInside = document.querySelector('.navbar').contains(event.target);
    if (!isClickInside) {
        document.querySelectorAll('.submenu').forEach(submenu => {
            submenu.classList.remove('show');
        });
    }
});
