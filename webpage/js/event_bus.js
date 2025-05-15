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

// Load content based on hash
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
    
    // First try HTMX
    try {
        htmx.ajax('GET', contentUrl, {
            target: '#content-area',
            swap: 'innerHTML',
            headers: {
                'HX-Request': 'true'
            }
        });
    } catch (e) {
        // If HTMX fails, try our fallback method
        console.warn("HTMX failed, using fallback", e);
        loadContent(contentUrl, contentArea);
    }
    
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

// Function to initialize clickable navigation
function initializeNavigation() {
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        // Make sure htmx processes this element
        htmx.process(link);
        
        // Add direct click handler as backup
        link.addEventListener('click', function(e) {
            const targetSelector = link.getAttribute('hx-target');
            const url = link.getAttribute('hx-get');
            const pushUrl = link.getAttribute('hx-push-url');
            
            if (targetSelector && url) {
                const target = document.querySelector(targetSelector);
                if (target) {
                    // Prevent default only if we're going to handle it
                    e.preventDefault();
                    
                    // Load content
                    loadContent(url, target).then(() => {
                        // Update URL if needed
                        if (pushUrl) {
                            history.pushState(null, null, pushUrl);
                        }
                        
                        // Update active nav item
                        updateActiveNavItem(pushUrl);
                    });
                }
            }
        });
    });
}

// Function to make index items clickable
function initializeIndexItems(container = document) {
    container.querySelectorAll('.index-item a').forEach(link => {
        // Make sure htmx processes this element
        htmx.process(link);
        
        // Add direct click handler as backup
        link.addEventListener('click', function(e) {
            const targetSelector = link.getAttribute('hx-target');
            const url = link.getAttribute('hx-get');
            const pushUrl = link.getAttribute('hx-push-url');
            
            if (targetSelector && url) {
                const target = document.querySelector(targetSelector);
                if (target) {
                    // Prevent default only if we're going to handle it
                    e.preventDefault();
                    
                    // Load content
                    loadContent(url, target).then(() => {
                        // Update URL if needed
                        if (pushUrl) {
                            history.pushState(null, null, pushUrl);
                        }
                    });
                }
            }
        });
    });
}

// SINGLE DOMContentLoaded handler - consolidated initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM content loaded");
    const contentArea = document.getElementById('content-area');
    
    // Ensure htmx is available and ready
    if (typeof htmx === 'undefined') {
        console.error("HTMX not loaded!");
        // Create a fallback version
        window.htmx = {
            process: function() { console.warn("HTMX not available for processing"); },
            ajax: function() { console.warn("HTMX not available for AJAX"); return Promise.reject(); }
        };
    }
    
    // Initialize navigation menu items
    initializeNavigation();
    
    // If directly accessing a URL with a hash, honor that
    if (window.location.hash) {
        console.log("Loading from hash:", window.location.hash);
        loadContentFromHash();
    } 
    // Otherwise load the default content
    else {
        console.log("No hash, loading default content");
        loadContent('/webpage/indexes/index-all.html', contentArea).then(() => {
            // Add the hash to the URL without triggering a new history entry
            history.replaceState(null, null, '#home');
            
            // Set appropriate active class on home navigation
            updateActiveNavItem('#home');
            
            // Initialize index items in the loaded content
            initializeIndexItems();
        });
    }
});

// Handle hash changes from browser navigation
window.addEventListener('hashchange', function() {
    console.log("Hash changed to:", window.location.hash);
    loadContentFromHash();
});

// Listen for HTMX events
document.body.addEventListener('htmx:afterSwap', function(event) {
    console.log("HTMX after swap");
    
    // Initialize any newly loaded index items
    initializeIndexItems(event.detail.target);
    
    // Update active nav for current hash
    const currentHash = window.location.hash || '#home';
    updateActiveNavItem(currentHash);
});

document.body.addEventListener('htmx:afterRequest', function(event) {
    console.log("HTMX after request");
    const elt = event.detail.elt;
    if (elt && elt.classList.contains('nav-item')) {
        const hash = elt.getAttribute('hx-push-url') || '';
        updateActiveNavItem(hash);
    }
});

// Handle errors in HTMX requests
document.body.addEventListener('htmx:responseError', function(event) {
    console.error("HTMX response error:", event);
    const contentArea = document.getElementById('content-area');
    loadContent('/webpage/indexes/index-all.html', contentArea);
});

// Enable touch handling for mobile
document.addEventListener('touchstart', function() {}, {passive: true});