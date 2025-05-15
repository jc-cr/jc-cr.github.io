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

// Load content based on hash on page load or hash change
function loadContentFromHash() {
    const hash = window.location.hash || '#home';
    const contentArea = document.getElementById('content-area');
    
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
    
    // Use HTMX to load the content
    htmx.ajax('GET', contentUrl, {
        target: '#content-area',
        swap: 'innerHTML',
        headers: {
            'HX-Request': 'true'
        }
    }).catch(() => {
        // If HTMX fails, try our fallback method
        loadContent('/webpage/indexes/index-all.html', contentArea);
    });
    
    // Update active navigation class
    updateActiveNavItem(hash);
}

// Update which navigation item is active
function updateActiveNavItem(hash) {
    // Remove active class from all nav items
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        link.classList.remove('active');
    });
    
    // For posts, we should highlight the corresponding tag if possible
    if (hash.startsWith('#post/')) {
        // We don't have an easy way to know which tag this post belongs to,
        // so we don't highlight any nav item
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

// Initialize page on load
document.addEventListener('DOMContentLoaded', function() {
    const contentArea = document.getElementById('content-area');
    
    // If directly accessing a URL with a hash, honor that
    if (window.location.hash) {
        loadContentFromHash();
    } 
    // Otherwise load the default content
    else {
        loadContent('/webpage/indexes/index-all.html', contentArea).then(() => {
            // Set appropriate active class on home navigation
            updateActiveNavItem('#home');
        });
    }
});

// Handle hash changes from browser navigation
window.addEventListener('hashchange', loadContentFromHash);

// Listen for HTMX events
document.body.addEventListener('htmx:afterSwap', function(event) {
    // Get the URL that was just navigated to
    const currentHash = window.location.hash || '#home';
    updateActiveNavItem(currentHash);
});

document.body.addEventListener('htmx:afterRequest', function(event) {
    const elt = event.detail.elt;
    if (elt && elt.classList.contains('nav-item')) {
        const hash = elt.getAttribute('hx-push-url') || '';
        updateActiveNavItem(hash);
    }
});

// Handle errors in HTMX requests
document.body.addEventListener('htmx:responseError', function(event) {
    const contentArea = document.getElementById('content-area');
    loadContent('/webpage/indexes/index-all.html', contentArea);
});
