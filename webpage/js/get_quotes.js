/**
 * quote_display.js - Loads SQLite database directly and displays random quotes
 */

class QuoteDisplay {
    constructor() {
        this.db = null;
        this.sqljs = null;
        this.isLoaded = false;
    }

    async loadDatabase() {
        if (this.isLoaded) {
            return true;
        }

        try {
            console.log('Starting database load...');
            
            // Load sql.js library (it should already be loaded from the HTML)
            if (typeof initSqlJs === 'undefined') {
                console.error('sql.js library not loaded');
                return false;
            }

            if (!this.sqljs) {
                console.log('Initializing sql.js...');
                this.sqljs = await initSqlJs({
                    locateFile: file => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/${file}`
                });
                console.log('sql.js initialized');
            }

            // Load the database file
            console.log('Fetching database file...');
            const response = await fetch('/data/forbes_quotes_rust.db');
            if (!response.ok) {
                console.error('Failed to load database:', response.status, response.statusText);
                return false;
            }

            console.log('Database file fetched, creating database...');
            const buffer = await response.arrayBuffer();
            this.db = new this.sqljs.Database(new Uint8Array(buffer));
            console.log('Database created successfully');

            // Test the database structure
            try {
                const tables = this.db.exec("SELECT name FROM sqlite_master WHERE type='table'");
                console.log('Database tables:', tables);
                
                const count = this.db.exec("SELECT COUNT(*) as count FROM quotes");
                console.log('Quote count:', count);
                
                // Test query
                const testQuery = this.db.exec("SELECT author, text FROM quotes LIMIT 1");
                console.log('Test query result:', testQuery);
            } catch (e) {
                console.error('Database structure test failed:', e);
            }

            this.isLoaded = true;
            console.log('Database fully loaded and tested');
            return true;
        } catch (error) {
            console.error('Error loading database:', error);
            return false;
        }
    }

    getRandomQuote() {
        if (!this.db) {
            console.log('Database not loaded');
            return {
                text: "Database not loaded",
                author: ""
            };
        }

        try {
            console.log('Executing random quote query...');
            
            // Try using exec instead of prepare for better compatibility
            const results = this.db.exec("SELECT author, text FROM quotes ORDER BY RANDOM() LIMIT 1");
            
            console.log('Query results:', results);
            
            if (results && results.length > 0 && results[0].values && results[0].values.length > 0) {
                const row = results[0].values[0];
                const author = row[0] || "Unknown";
                const text = row[1];
                
                console.log('Selected quote:', { author, text });
                
                return {
                    text: text,
                    author: author
                };
            } else {
                console.log('No results from query');
                return {
                    text: "No quotes available",
                    author: ""
                };
            }
        } catch (error) {
            console.error('Error querying database:', error);
            return {
                text: "Error loading quote: " + error.message,
                author: ""
            };
        }
    }

    createQuoteHTML(quote) {
        const authorHtml = quote.author && quote.author !== "Unknown" && quote.author.trim() !== "" 
            ? `<div class="quote-author">— ${quote.author}</div>` 
            : '';

        return `
            <div class="quote-container">
                <h2>Random Quote</h2>
                <div class="quote-item">
                    <div class="quote-text">"${quote.text}"</div>
                    ${authorHtml}
                </div>
            </div>
        `;
    }

    async displayRandomQuote(targetElement) {
        if (!targetElement) {
            console.error('No target element provided for quote display');
            return;
        }

        console.log('Displaying random quote...');

        // Show loading state
        targetElement.innerHTML = this.createQuoteHTML({
            text: "Loading quote...",
            author: ""
        });

        // Load database if not already loaded
        const loaded = await this.loadDatabase();
        if (!loaded) {
            targetElement.innerHTML = this.createQuoteHTML({
                text: "Unable to load quotes at this time.",
                author: ""
            });
            return;
        }

        // Display random quote
        const randomQuote = this.getRandomQuote();
        targetElement.innerHTML = this.createQuoteHTML(randomQuote);
        console.log('Quote displayed');
    }
}

// Create global instance
window.quoteDisplay = new QuoteDisplay();

// Function to initialize quote display
function initializeQuoteDisplay() {
    console.log('Initializing quote display...');
    const quoteSection = document.getElementById('quote-section');
    if (quoteSection) {
        console.log('Quote section found, displaying quote');
        if (window.quoteDisplay) {
            window.quoteDisplay.displayRandomQuote(quoteSection);
        }
    } else {
        console.log('Quote section not found');
    }
}

// Function to check if we're on the home page content
function isHomeContent() {
    const contentArea = document.getElementById('content-area');
    if (contentArea) {
        return contentArea.innerHTML.includes('quote-section') || contentArea.innerHTML.includes('Latest');
    }
    return false;
}

// Initialize when content is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM content loaded');
    // Small delay to ensure content is loaded
    setTimeout(() => {
        if (isHomeContent()) {
            initializeQuoteDisplay();
        }
    }, 200);
});

// Also initialize when content is loaded via HTMX (for home page)
document.body.addEventListener('htmx:afterSwap', function(event) {
    console.log('HTMX after swap event');
    // Only run for home/index content
    if (event.detail.target && event.detail.target.id === 'content-area') {
        // Check if the loaded content contains the quote section
        if (event.detail.target.innerHTML.includes('quote-section')) {
            console.log('Home content detected, initializing quotes');
            setTimeout(initializeQuoteDisplay, 100);
        }
    }
});

// Listen for hash changes to reinitialize quotes on home
window.addEventListener('hashchange', function() {
    const hash = window.location.hash || '#home';
    if (hash === '#home') {
        setTimeout(() => {
            if (isHomeContent()) {
                initializeQuoteDisplay();
            }
        }, 300);
    }
});