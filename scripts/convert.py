#!/usr/bin/env python3
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
import argparse

def update_media_urls(base_dir=None, dry_run=False):
    """
    Update only the media URLs in all post.html files
    
    Args:
        base_dir: Base directory of the website
        dry_run: If True, don't actually modify files, just print what would be done
    """
    base_dir = Path(base_dir if base_dir else '.')
    posts_dir = base_dir / 'webpage' / 'posts'
    
    # Counter for tracking updates
    updated = 0
    skipped = 0
    errors = 0
    
    # Find all post.html files
    for post_dir in posts_dir.glob('*/'):
        post_file = post_dir / 'post.html'
        
        # Skip if post.html doesn't exist
        if not post_file.exists():
            print(f"Skipping {post_dir.name}: No post.html found")
            skipped += 1
            continue
            
        try:
            # Read the current post.html
            with open(post_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse the HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Track if we made any changes
            changes_made = False
            
            # Fix image paths to be absolute
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if src and not src.startswith('/') and not src.startswith('http'):
                    # It's a relative path, make it absolute
                    img['src'] = f"/webpage/posts/{post_dir.name}/{src}"
                    changes_made = True
                    
            # Fix video source paths
            for source in soup.find_all('source'):
                src = source.get('src', '')
                if src and not src.startswith('/') and not src.startswith('http'):
                    # It's a relative path, make it absolute
                    source['src'] = f"/webpage/posts/{post_dir.name}/{src}"
                    changes_made = True
            
            # Only update if changes were made
            if changes_made:
                if not dry_run:
                    # Save the updated post.html
                    with open(post_file, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                    
                    updated += 1
                    print(f"Updated media URLs in {post_dir.name}")
                else:
                    print(f"Would update media URLs in {post_dir.name} (dry run)")
                    updated += 1
            else:
                print(f"No URL updates needed for {post_dir.name}")
                skipped += 1
                
        except Exception as e:
            print(f"Error updating {post_dir.name}: {e}")
            errors += 1
    
    # Print summary
    print(f"\nSummary: Updated {updated} posts, skipped {skipped}, encountered {errors} errors")
    if dry_run:
        print("Dry run completed. No files were modified.")
    return updated, skipped, errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update media URLs in posts")
    parser.add_argument('--base-dir', help="Base directory of the website (default: current directory)")
    parser.add_argument('--dry-run', '-n', action='store_true', help="Don't modify files, just print what would be done")
    args = parser.parse_args()
    
    update_media_urls(args.base_dir, args.dry_run)