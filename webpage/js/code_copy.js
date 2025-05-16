/**
 * code-copy.js - Adds copy buttons to code blocks
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize copy buttons on page load
    initializeCodeCopyButtons();
});

// Also initialize when content is loaded via HTMX
document.body.addEventListener('htmx:afterSwap', function(event) {
    // Initialize copy buttons after HTMX content swap
    initializeCodeCopyButtons(event.detail.target);
});

function initializeCodeCopyButtons(container = document) {
    // Find all pre elements in the container
    const codeBlocks = container.querySelectorAll('pre');
    
    codeBlocks.forEach(pre => {
        // Check if it already has a copy button
        if (pre.querySelector('.copy-button')) {
            return;
        }
        
        // Create copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.setAttribute('aria-label', 'Copy code to clipboard');
        copyButton.setAttribute('type', 'button');
        
        // Add click event
        copyButton.addEventListener('click', function() {
            // Get the text content
            const code = pre.querySelector('code') || pre;
            const text = code.textContent;
            
            // Copy to clipboard using the Clipboard API
            navigator.clipboard.writeText(text).then(() => {
                // Visual feedback on success
                copyButton.setAttribute('data-copied', 'true');
                
                // Reset the button after a delay
                setTimeout(() => {
                    copyButton.removeAttribute('data-copied');
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
                alert('Failed to copy code to clipboard');
            });
        });
        
        // Add button to the pre element
        pre.appendChild(copyButton);
    });
}