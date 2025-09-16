/**
 * event-bus.js
 */

// Navigation context tracking
const NavigationContext = {
    currentContext: 'all', // 'all', 'project', 'paper', 'blog', 'haikuesque'
    posts: [], // Array of post objects in current context
    currentPostIndex: -1,
    contextPosts: {}, // Cache posts for each context
    
    setContext(context, posts) {
        this.currentContext = context;
        this.posts = posts || [];
        this.contextPosts[context] = posts || [];
        console.log('Navigation context set:', context, 'Posts:', this.posts.length);
    },
    
    setCurrentPost(postPath) {
        this.currentPostIndex = this.posts.findIndex(post => post.path === postPath);
        console.log('Current post index:', this.currentPostIndex, 'of', this.posts.length, 'in context:', this.currentContext);
    },
    
    // Determine context from current hash and maintain it
    determineContextFromHash(hash) {
        if (hash.startsWith('#post/')) {
            // For posts, keep the current context or determine from available contexts
            return this.currentContext;
        } else if (hash === '#project') {
            return 'project';
        } else if (hash === '#paper') {
            return 'paper';
        } else if (hash === '#pennings') {
            return 'pennings';
        } else {
            return 'all';
        }
    },
    
    // Load posts for a specific context if not cached
async loadContextPosts(context) {
    if (this.contextPosts[context]) {
        this.setContext(context, this.contextPosts[context]);
        return this.contextPosts[context];
    }
    
    // Determine the correct index URL for the context
    let indexUrl;
    switch (context) {
        case 'project':
            indexUrl = '/webpage/indexes/index-project.html';
            break;
        case 'paper':
            indexUrl = '/webpage/indexes/index-paper.html';
            break;
        case 'pennings':  // Add this case
            indexUrl = '/webpage/indexes/index-pennings.html';
            break;
        case 'all':
        default:
            indexUrl = '/webpage/indexes/index-all.html';
            break;
    }
    
    try {
        const response = await fetch(indexUrl);
        if (response.ok) {
            const html = await response.text();
            const posts = this.extractPostsFromHTML(html);
            this.setContext(context, posts);
            return posts;
        }
    } catch (error) {
        console.error('Error loading context posts:', error);
    }
    
    return [];
},
    
    // Extract posts from HTML content
    extractPostsFromHTML(html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        const posts = [];
        const indexItems = tempDiv.querySelectorAll('.index-item');
        
        indexItems.forEach(item => {
            const link = item.querySelector('a[hx-push-url]');
            if (link) {
                const pushUrl = link.getAttribute('hx-push-url');
                const postPath = pushUrl.replace('#post/', '');
                const title = link.textContent.trim();
                
                posts.push({
                    path: postPath,
                    title: title,
                    url: link.getAttribute('hx-get')
                });
            }
        });
        
        return posts;
    },
    
    // Find which context contains a specific post
async findPostContext(postPath) {
    const contexts = ['project', 'paper', 'pennings', 'all'];  // Replace blog/haikuesque with pennings
    
    for (const context of contexts) {
        await this.loadContextPosts(context);
        if (this.contextPosts[context] && 
            this.contextPosts[context].some(post => post.path === postPath)) {
            return context;
        }
    }
    
    return 'all'; // Default fallback
},
    
    getPreviousPost() {
        if (this.currentPostIndex > 0) {
            return this.posts[this.currentPostIndex - 1];
        }
        return null;
    },
    
    getNextPost() {
        if (this.currentPostIndex >= 0 && this.currentPostIndex < this.posts.length - 1) {
            return this.posts[this.currentPostIndex + 1];
        }
        return null;
    }
};

// Enhanced content loading with context extraction
async function loadContent(url, targetElement) {
    try {
        const response = await fetch(url);
        
        if (response.ok) {
            const html = await response.text();
            targetElement.innerHTML = html;
            
            // Process any htmx attributes in the loaded content
            htmx.process(targetElement);
            
            // Initialize any new index items and extract navigation context
            if (html.includes('index-container')) {
                initializeIndexItems(targetElement);
                extractNavigationContext(html, url);
            }
            
            // Initialize quotes if this is home content
            if (html.includes('quote-section')) {
                console.log('Home content loaded, initializing quotes');
                setTimeout(() => {
                    if (typeof window.quoteDisplay !== 'undefined') {
                        const quoteSection = document.getElementById('quote-section');
                        if (quoteSection) {
                            window.quoteDisplay.displayRandomQuote(quoteSection);
                        }
                    }
                }, 100);
            }
            
            return true;
        } else {
            console.warn(`Failed to load ${url}, status: ${response.status}`);
            if (url !== '/webpage/indexes/index-all.html') {
                return loadContent('/webpage/indexes/index-all.html', targetElement);
            }
            return false;
        }
    } catch (error) {
        console.error(`Error loading ${url}:`, error);
        if (url !== '/webpage/indexes/index-all.html') {
            return loadContent('/webpage/indexes/index-all.html', targetElement);
        }
        return false;
    }
}

// Extract navigation context from index pages
function extractNavigationContext(html, url) {
    // Determine context from URL
    let context = 'all';
    if (url.includes('index-project.html')) context = 'project';
    else if (url.includes('index-paper.html')) context = 'paper';
    else if (url.includes('index-blog.html')) context = 'blog';
    else if (url.includes('index-haikuesque.html')) context = 'haikuesque';
    
    // Extract post data from index items
    const posts = NavigationContext.extractPostsFromHTML(html);
    NavigationContext.setContext(context, posts);
}

// Create navigation for posts (bottom of content for all screen sizes)
async function createNavigationOverlays() {
    // Remove existing navigation
    document.querySelectorAll('.post-navigation').forEach(el => el.remove());
    
    const contentArea = document.getElementById('content-area');
    if (!contentArea) return;
    
    // Get current post path from URL
    const hash = window.location.hash;
    if (!hash.startsWith('#post/')) return;
    
    const currentPostPath = hash.substring(6);
    
    // Ensure we have the correct context loaded
    await ensureCorrectContext(currentPostPath);
    
    NavigationContext.setCurrentPost(currentPostPath);
    
    const prevPost = NavigationContext.getPreviousPost();
    const nextPost = NavigationContext.getNextPost();
    
    console.log('Creating navigation in context:', NavigationContext.currentContext);
    console.log('Previous post:', prevPost?.title || 'None');
    console.log('Next post:', nextPost?.title || 'None');
    
    // Create bottom navigation for all screen sizes
    createPostNavigation(prevPost, nextPost);
}

// Create unified post navigation at bottom of content
function createPostNavigation(prevPost, nextPost) {
    const contentArea = document.getElementById('content-area');
    if (!contentArea) return;
    
    // Create navigation container
    const nav = document.createElement('nav');
    nav.className = 'post-navigation';
    nav.setAttribute('aria-label', 'Post navigation');
    
    // Add class for single navigation (when only prev or next exists)
    if ((!prevPost && nextPost) || (prevPost && !nextPost)) {
        nav.classList.add('single');
    }
    
    // Create previous button
    if (prevPost) {
        const prevButton = createNavButton('prev', prevPost);
        nav.appendChild(prevButton);
    }
    
    // Create next button  
    if (nextPost) {
        const nextButton = createNavButton('next', nextPost);
        nav.appendChild(nextButton);
    }
    
    // Append to content area
    contentArea.appendChild(nav);
}

// Create individual navigation button
function createNavButton(direction, post) {
    const button = document.createElement('button');
    button.className = `nav-button ${direction}`;
    button.setAttribute('aria-label', `${direction === 'prev' ? 'Previous' : 'Next'} post: ${post.title}`);
    
    const arrow = document.createElement('span');
    arrow.className = 'nav-arrow';
    arrow.textContent = direction === 'prev' ? '←' : '→';
    
    const content = document.createElement('div');
    content.className = 'nav-content';
    
    const label = document.createElement('div');
    label.className = 'nav-label';
    label.textContent = direction === 'prev' ? 'Previous' : 'Next';
    
    const title = document.createElement('div');
    title.className = 'nav-title';
    title.textContent = post.title;
    
    content.appendChild(label);
    content.appendChild(title);
    
    // Arrange arrow and content based on direction
    if (direction === 'prev') {
        button.appendChild(arrow);
        button.appendChild(content);
    } else {
        button.appendChild(content);
        button.appendChild(arrow);
    }
    
    // Add click handler
    const navigateHandler = () => navigateToPost(post);
    button.addEventListener('click', navigateHandler);
    
    return button;
}

// Ensure we have the correct context for the current post
async function ensureCorrectContext(postPath) {
    const currentHash = window.location.hash;
    let targetContext = NavigationContext.determineContextFromHash(currentHash);
    
    // If we're viewing a post but don't have a specific context, 
    // try to find which context this post belongs to
    if (currentHash.startsWith('#post/') && NavigationContext.currentContext === 'all') {
        // Check if we can determine context from the post itself
        const contextFromPost = await NavigationContext.findPostContext(postPath);
        if (contextFromPost !== 'all') {
            targetContext = contextFromPost;
        }
    }
    
    // Load the context if we don't have it or if it's different
    if (NavigationContext.currentContext !== targetContext || 
        !NavigationContext.contextPosts[targetContext]) {
        await NavigationContext.loadContextPosts(targetContext);
    }
}

// Create individual navigation overlay
function createNavOverlay(direction, post) {
    const overlay = document.createElement('div');
    overlay.className = `page-nav-overlay page-nav-${direction}`;
    overlay.setAttribute('tabindex', '0');
    overlay.setAttribute('role', 'button');
    overlay.setAttribute('aria-label', `${direction === 'prev' ? 'Previous' : 'Next'} post: ${post.title}`);
    
    // Create content
    const content = document.createElement('div');
    content.className = 'page-nav-content';
    
    const arrow = document.createElement('div');
    arrow.className = 'page-nav-arrow';
    arrow.innerHTML = direction === 'prev' ? '‹' : '›';
    
    const text = document.createElement('div');
    text.className = 'page-nav-text';
    text.innerHTML = `
        <div class="page-nav-label">${direction === 'prev' ? 'Previous' : 'Next'}</div>
        <div class="page-nav-title">${post.title}</div>
    `;
    
    content.appendChild(arrow);
    content.appendChild(text);
    overlay.appendChild(content);
    
    // Add click handler
    const navigateHandler = () => navigateToPost(post);
    overlay.addEventListener('click', navigateHandler);
    overlay.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            navigateHandler();
        }
    });
    
    return overlay;
}

// Navigate to a post using HTMX
function navigateToPost(post) {
    const contentArea = document.getElementById('content-area');
    if (!contentArea) return;
    
    // Use HTMX to navigate
    htmx.ajax('GET', post.url, {
        target: '#content-area',
        swap: 'innerHTML'
    });
    
    // Update URL
    window.history.pushState(null, '', `#post/${post.path}`);
    
    // Create overlays after a short delay to allow content to load
    setTimeout(createNavigationOverlays, 100);
}

// Enhanced load content from hash
async function loadContentFromHash() {
    const hash = window.location.hash || '#home';
    const contentArea = document.getElementById('content-area');
    
    if (!contentArea) return;
    
    let contentUrl;
    
    // Check if it's a post URL (format: #post/YYYYMMDD_title)
    if (hash.startsWith('#post/')) {
        const postPath = hash.substring(6);
        contentUrl = `/webpage/posts/${postPath}/post.html`;
    } else {
        // It's a regular navigation URL - update context
        const context = NavigationContext.determineContextFromHash(hash);
        await NavigationContext.loadContextPosts(context);
        
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
            case '#pennings':  // Add this case
                contentUrl = '/webpage/indexes/index-pennings.html';
                break;
            case '#home':
            default:
                contentUrl = '/webpage/indexes/index-all.html';
        }
    }
    
    // Load content and update navigation
    loadContent(contentUrl, contentArea).then(() => {
        updateActiveNavItem(hash);
        
        // Create navigation overlays for posts
        if (hash.startsWith('#post/')) {
            setTimeout(createNavigationOverlays, 150);
        }
    });
}

// Update which navigation item is active
function updateActiveNavItem(hash) {
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        link.classList.remove('active');
    });
    
    if (hash.startsWith('#post/')) {
        return;
    }
    
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
        htmx.process(link);
        link.removeEventListener('click', handleNavClick);
        link.addEventListener('click', handleNavClick);
    });
}

// Navigation click handler
function handleNavClick(e) {
    const link = e.currentTarget;
    const pushUrl = link.getAttribute('hx-push-url');
    
    // Update context when navigating to tag pages
    if (pushUrl) {
        const context = NavigationContext.determineContextFromHash(pushUrl);
        NavigationContext.loadContextPosts(context);
    }
}

// Function to make index items clickable
function initializeIndexItems(container = document) {
    container.querySelectorAll('.index-item a').forEach(link => {
        htmx.process(link);
        link.removeEventListener('click', handleIndexClick);
        link.addEventListener('click', handleIndexClick);
    });
}

// Index click handler - maintains context when clicking on posts
function handleIndexClick(e) {
    const link = e.currentTarget;
    const pushUrl = link.getAttribute('hx-push-url');
    
    // When clicking on a post from an index, the context should remain the same
    // This ensures that navigation within posts stays in the same tag category
    console.log('Index item clicked, maintaining context:', NavigationContext.currentContext);
}

// Enhanced DOMContentLoaded handler
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM content loaded");
    const contentArea = document.getElementById('content-area');
    
    if (!contentArea) {
        console.error("Content area not found!");
        return;
    }
    
    if (typeof htmx === 'undefined') {
        console.error("HTMX not loaded!");
        return;
    }
    
    initializeNavigation();
    loadContentFromHash();
});

// Handle hash changes
window.addEventListener('hashchange', function(e) {
    console.log("Hash changed to:", window.location.hash);
    e.preventDefault();
    loadContentFromHash();
});

// Enhanced HTMX event listeners
document.body.addEventListener('htmx:afterSwap', function(event) {
    console.log("HTMX after swap");
    
    initializeIndexItems(event.detail.target);
    
    if (event.detail.target && event.detail.target.innerHTML.includes('quote-section')) {
        console.log('HTMX loaded home content, initializing quotes');
        setTimeout(() => {
            if (typeof window.quoteDisplay !== 'undefined') {
                const quoteSection = document.getElementById('quote-section');
                if (quoteSection) {
                    window.quoteDisplay.displayRandomQuote(quoteSection);
                }
            }
        }, 100);
    }
    
    // Create navigation overlays for posts
    const currentHash = window.location.hash || '#home';
    if (currentHash.startsWith('#post/')) {
        setTimeout(createNavigationOverlays, 150);
    }
    
    updateActiveNavItem(currentHash);
});

document.body.addEventListener('htmx:pushedIntoHistory', function(event) {
    console.log("HTMX pushed into history:", event.detail);
    const currentHash = window.location.hash || '#home';
    updateActiveNavItem(currentHash);
    
    if (currentHash.startsWith('#post/')) {
        setTimeout(createNavigationOverlays, 150);
    }
});

document.body.addEventListener('htmx:responseError', function(event) {
    console.error("HTMX response error:", event);
    const contentArea = document.getElementById('content-area');
    if (contentArea) {
        loadContent('/webpage/indexes/index-all.html', contentArea).then(() => {
            window.location.hash = '#home';
        });
    }
});

window.addEventListener('popstate', function(event) {
    console.log("Popstate event:", event);
    loadContentFromHash();
});

// Keyboard navigation support
document.addEventListener('keydown', function(e) {
    // Only handle keyboard nav when viewing a post
    const hash = window.location.hash;
    if (!hash.startsWith('#post/')) return;
    
    if (e.key === 'ArrowLeft') {
        const prevPost = NavigationContext.getPreviousPost();
        if (prevPost) {
            e.preventDefault();
            navigateToPost(prevPost);
        }
    } else if (e.key === 'ArrowRight') {
        const nextPost = NavigationContext.getNextPost();
        if (nextPost) {
            e.preventDefault();
            navigateToPost(nextPost);
        }
    }
});

// Navigate to a post using HTMX
function navigateToPost(post) {
    const contentArea = document.getElementById('content-area');
    if (!contentArea) return;
    
    // Use HTMX to navigate
    htmx.ajax('GET', post.url, {
        target: '#content-area',
        swap: 'innerHTML'
    });
    
    // Update URL
    window.history.pushState(null, '', `#post/${post.path}`);
    
    // Create navigation after a short delay to allow content to load
    setTimeout(createNavigationOverlays, 100);
}

document.addEventListener('touchstart', function() {}, {passive: true});

// Handle window resize to switch between mobile and desktop navigation
let resizeTimeout;
window.addEventListener('resize', function() {
    // Debounce resize events
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        const hash = window.location.hash;
        if (hash.startsWith('#post/')) {
            // Recreate navigation with appropriate style for new screen size
            createNavigationOverlays();
        }
    }, 250);
});