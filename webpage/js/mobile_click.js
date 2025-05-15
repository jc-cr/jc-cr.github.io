// Simple, direct implementation for mobile menu toggle
(function() {
    // Run immediately when the script loads
    const menuToggle = document.getElementById('menu-toggle');
    const body = document.body;
    
    if (menuToggle) {
        // Direct click handler
        menuToggle.onclick = function() {
            console.log('Menu toggle clicked');
            body.classList.toggle('sidebar-open');
        };
        
        // Close menu when a link is clicked
        document.querySelectorAll('.sidebar a').forEach(function(link) {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 768) {
                    body.classList.remove('sidebar-open');
                }
            });
        });
    }
})();