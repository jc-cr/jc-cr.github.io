/**
 * event-bus.js - Handles navigation and content loading
 */

// Helper function to safely load content with fallback
async function loadContent(url, targetElement) {
    try {
        const response = await fetch(url);
        
        if (response.ok) {
            const html = await response.text();
            targetElement.innerHTML = html;
            
            // Process any htmx attributes in the loaded content
            htmx.process(targetElement);
            
            // Initialize any new index items in the loaded content
            initializeIndexItems(targetElement);
            
            return true;
        } else {
            console.warn(`Failed to load ${url}, status: ${response.status}`);
            // If we fail to load and it's not the index content, try to load index content as fallback
            if (url !== '/webpage/indexes/index-all.html') {
                return loadContent('/webpage/indexes/index-all.html', targetElement);
            }
            return false;
        }
    } catch (error) {
        console.error(`Error loading ${url}:`, error);
        // If there's an error and it's not the index content, try to load index content as fallback
        if (url !== '/webpage/indexes/index-all.html') {
            return loadContent('/webpage/indexes/index-all.html', targetElement);
        }
        return false;
    }
}

// Load content based on hash - simplified version
function loadContentFromHash() {
    const hash = window.location.hash || '#home';
    const contentArea = document.getElementById('content-area');
    
    if (!contentArea) return;
    
    let contentUrl;
    
    // Check if it's a post URL (format: #post/YYYYMMDD_title)
    if (hash.startsWith('#post/')) {
        const postPath = hash.substring(6); // Remove '#post/' prefix
        contentUrl = `/webpage/posts/${postPath}/post.html`;
    } else {
        // It's a regular navigation URL
        switch(hash) {
            case '#about':
                contentUrl = '/webpage/about/about-content.html';
                break;
            case '#project':
                contentUrl = '/webpage/indexes/index-project.html';
                break;
            case '#paper':
                contentUrl = '/webpage/indexes/index-paper.html';
                break;
            case '#blog':
                contentUrl = '/webpage/indexes/index-blog.html';
                break;
            case '#haikuesque':
                contentUrl = '/webpage/indexes/index-haikuesque.html';
                break;
            case '#home':
            default: // #home or empty
                contentUrl = '/webpage/indexes/index-all.html';
        }
    }
    
    // Load content and update navigation
    loadContent(contentUrl, contentArea).then(() => {
        updateActiveNavItem(hash);
    });
}

// Update which navigation item is active
function updateActiveNavItem(hash) {
    // Remove active class from all nav items
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        link.classList.remove('active');
    });
    
    // For posts, we don't highlight any nav item
    if (hash.startsWith('#post/')) {
        return;
    }
    
    // Add active class to the matching nav item
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        const hrefTarget = link.getAttribute('hx-push-url') || '';
        if (hrefTarget === hash) {
            link.classList.add('active');
        }
    });
}

// Function to initialize clickable navigation - removed manual history management
function initializeNavigation() {
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        // Make sure htmx processes this element
        htmx.process(link);
        
        // Remove any existing click handlers to avoid conflicts
        link.removeEventListener('click', handleNavClick);
        
        // Add click handler only as backup if HTMX fails
        link.addEventListener('click', handleNavClick);
    });
}

// Simplified click handler that doesn't interfere with HTMX
function handleNavClick(e) {
    const link = e.currentTarget;
    const targetSelector = link.getAttribute('hx-target');
    const url = link.getAttribute('hx-get');
    const pushUrl = link.getAttribute('hx-push-url');
    
    // Only handle if HTMX attributes are present but HTMX fails
    if (targetSelector && url && pushUrl) {
        // Let HTMX handle it first
        return;
    }
}

// Function to make index items clickable - simplified
function initializeIndexItems(container = document) {
    container.querySelectorAll('.index-item a').forEach(link => {
        // Make sure htmx processes this element
        htmx.process(link);
        
        // Remove any existing handlers
        link.removeEventListener('click', handleIndexClick);
        link.addEventListener('click', handleIndexClick);
    });
}

// Simplified index click handler
function handleIndexClick(e) {
    const link = e.currentTarget;
    const targetSelector = link.getAttribute('hx-target');
    const url = link.getAttribute('hx-get');
    
    // Only handle if HTMX attributes are present
    if (targetSelector && url) {
        // Let HTMX handle it
        return;
    }
}

// SINGLE DOMContentLoaded handler - simplified
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM content loaded");
    const contentArea = document.getElementById('content-area');
    
    if (!contentArea) {
        console.error("Content area not found!");
        return;
    }
    
    // Ensure htmx is available
    if (typeof htmx === 'undefined') {
        console.error("HTMX not loaded!");
        return;
    }
    
    // Initialize navigation menu items
    initializeNavigation();
    
    // Load initial content based on current hash
    loadContentFromHash();
});

// Handle hash changes from browser navigation (back/forward buttons)
window.addEventListener('hashchange', function(e) {
    console.log("Hash changed to:", window.location.hash);
    // Prevent default and let our handler manage it
    e.preventDefault();
    loadContentFromHash();
});

// Listen for HTMX events - simplified
document.body.addEventListener('htmx:afterSwap', function(event) {
    console.log("HTMX after swap");
    
    // Initialize any newly loaded index items
    initializeIndexItems(event.detail.target);
    
    // Update active nav for current hash
    const currentHash = window.location.hash || '#home';
    updateActiveNavItem(currentHash);
});

// Handle HTMX navigation completion
document.body.addEventListener('htmx:pushedIntoHistory', function(event) {
    console.log("HTMX pushed into history:", event.detail);
    // Update active navigation when HTMX updates the URL
    const currentHash = window.location.hash || '#home';
    updateActiveNavItem(currentHash);
});

// Handle errors in HTMX requests
document.body.addEventListener('htmx:responseError', function(event) {
    console.error("HTMX response error:", event);
    const contentArea = document.getElementById('content-area');
    if (contentArea) {
        loadContent('/webpage/indexes/index-all.html', contentArea).then(() => {
            // Navigate to home on error
            window.location.hash = '#home';
        });
    }
});

// Handle browser back/forward buttons more reliably
window.addEventListener('popstate', function(event) {
    console.log("Popstate event:", event);
    // Load content based on current URL hash
    loadContentFromHash();
});

// Enable touch handling for mobile
document.addEventListener('touchstart', function() {}, {passive: true});