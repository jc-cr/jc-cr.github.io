/**
 * search.js - Simple search functionality using Fuse.js
 */

class SiteSearch {
    constructor() {
        this.searchData = [];
        this.fuse = null;
        this.isInitialized = false;
        this.overlay = null;
        this.searchInput = null;
        this.resultsContainer = null;
    }

    async initialize() {
        if (this.isInitialized) return;

        // Load search data
        try {
            const response = await fetch('/webpage/search.json');
            if (!response.ok) {
                console.error('Failed to load search data');
                return;
            }
            this.searchData = await response.json();

            // Initialize Fuse.js with search options
            const options = {
                keys: ['title', 'snippet', 'tags'],
                threshold: 0.3,
                includeMatches: true,
                minMatchCharLength: 2
            };

            this.fuse = new Fuse(this.searchData, options);
            this.isInitialized = true;
            console.log('Search initialized with', this.searchData.length, 'posts');
        } catch (error) {
            console.error('Error initializing search:', error);
        }
    }

    createSearchUI() {
        // Create search icon button
        const searchIcon = document.createElement('button');
        searchIcon.id = 'search-icon';
        searchIcon.className = 'search-icon';
        searchIcon.setAttribute('aria-label', 'Open search');
        searchIcon.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
            </svg>
        `;

        // Create search overlay
        this.overlay = document.createElement('div');
        this.overlay.id = 'search-overlay';
        this.overlay.className = 'search-overlay';
        this.overlay.innerHTML = `
            <div class="search-overlay-content">
                <div class="search-header">
                    <input type="text" id="search-input" class="search-input" placeholder="Search posts..." autocomplete="off" />
                    <button id="search-close" class="search-close" aria-label="Close search">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                <div id="search-results" class="search-results">
                    <div class="search-hint">Start typing to search posts...</div>
                </div>
            </div>
        `;

        // Add to body (not content-area to avoid HTMX removal)
        document.body.appendChild(searchIcon);
        document.body.appendChild(this.overlay);

        this.searchInput = document.getElementById('search-input');
        this.resultsContainer = document.getElementById('search-results');

        // Add event listeners
        searchIcon.addEventListener('click', () => this.openSearch());
        document.getElementById('search-close').addEventListener('click', () => this.closeSearch());
        this.searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.closeSearch();
            }
        });

        // Keyboard shortcut: Escape to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.overlay.classList.contains('active')) {
                this.closeSearch();
            }
        });
    }

    openSearch() {
        this.overlay.classList.add('active');
        this.searchInput.focus();
    }

    closeSearch() {
        this.overlay.classList.remove('active');
        this.searchInput.value = '';
        this.resultsContainer.innerHTML = '<div class="search-hint">Start typing to search posts...</div>';
    }

    handleSearch(query) {
        if (!this.fuse) {
            console.error('Search not initialized');
            return;
        }

        if (query.trim().length < 2) {
            this.resultsContainer.innerHTML = '<div class="search-hint">Type at least 2 characters to search...</div>';
            return;
        }

        const results = this.fuse.search(query);

        if (results.length === 0) {
            this.resultsContainer.innerHTML = '<div class="search-hint">No results found.</div>';
            return;
        }

        // Display results
        let html = '';
        results.forEach(result => {
            const post = result.item;
            const matches = result.matches || [];

            // Get the best match for highlighting
            let displayTitle = post.title;
            let displaySnippet = post.snippet;

            // Highlight matches in title
            const titleMatch = matches.find(m => m.key === 'title');
            if (titleMatch) {
                displayTitle = this.highlightMatches(post.title, titleMatch.indices);
            }

            // Highlight matches in snippet
            const snippetMatch = matches.find(m => m.key === 'snippet');
            if (snippetMatch) {
                displaySnippet = this.highlightMatches(post.snippet, snippetMatch.indices);
            }

            html += `
                <div class="search-result-item">
                    <a href="#post/${post.path}" class="search-result-link" data-url="${post.url}">
                        <div class="search-result-title">${displayTitle}</div>
                        <div class="search-result-snippet">${displaySnippet}</div>
                        <div class="search-result-meta">
                            ${post.tags.map(tag => `<span class="tag">${tag}</span>`).join(' ')}
                        </div>
                    </a>
                </div>
            `;
        });

        this.resultsContainer.innerHTML = html;

        // Add click handlers to results
        this.resultsContainer.querySelectorAll('.search-result-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const url = link.getAttribute('data-url');
                const path = link.getAttribute('href');
                
                // Use HTMX to navigate
                htmx.ajax('GET', url, {
                    target: '#content-area',
                    swap: 'innerHTML'
                });
                
                window.history.pushState(null, '', path);
                this.closeSearch();
            });
        });
    }

    highlightMatches(text, indices) {
        if (!indices || indices.length === 0) return text;

        let result = '';
        let lastIndex = 0;

        // Sort indices by start position
        const sortedIndices = [...indices].sort((a, b) => a[0] - b[0]);

        sortedIndices.forEach(([start, end]) => {
            // Add text before match
            result += text.substring(lastIndex, start);
            // Add highlighted match
            result += `<mark>${text.substring(start, end + 1)}</mark>`;
            lastIndex = end + 1;
        });

        // Add remaining text
        result += text.substring(lastIndex);

        return result;
    }
}

// Initialize search when DOM is ready
let siteSearch = null;

document.addEventListener('DOMContentLoaded', async function() {
    siteSearch = new SiteSearch();
    await siteSearch.initialize();
    
    // Wait a bit for content to load, then add search UI
    setTimeout(() => {
        siteSearch.createSearchUI();
    }, 500);
});

// Also initialize after HTMX swaps if search wasn't initialized yet
document.body.addEventListener('htmx:afterSwap', function(event) {
    // Only initialize if search hasn't been set up yet
    if (!siteSearch || !document.getElementById('search-icon')) {
        if (siteSearch && siteSearch.isInitialized) {
            setTimeout(() => {
                siteSearch.createSearchUI();
            }, 100);
        }
    }
});