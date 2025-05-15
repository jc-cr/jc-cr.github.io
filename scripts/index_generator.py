#!/usr/bin/env python3
import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class IndexGenerator:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir if base_dir else '/app')
        self.posts_dir = self.base_dir / 'webpage/posts'
        self.indexes_dir = self.base_dir / 'webpage/indexes'
        
        # Ensure indexes directory exists
        self.indexes_dir.mkdir(exist_ok=True, parents=True)
        
        # Templates for index files - Updated to use HTMX for post links
        self.index_item_template = """
<div class="index-item">
    <div class="index-date-tags">
        {date_formatted} · Tagged with {tags}
    </div>
    <h3 class="index-title"><a hx-get="{post_url}" hx-target="#content-area" hx-push-url="#post/{post_path}">{title}</a></h3>
    <div class="index-snippet">
        {snippet}
    </div>
</div>
"""
        
        self.index_template = """<h2>{title}</h2>
<div class="index-container">
{items}
</div>
"""

    def _format_date(self, date_str):
        """Format date from YYYY-MM-DD to "5th of April, 2025" format"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # Get day with ordinal suffix
            day = date_obj.day
            if 4 <= day <= 20 or 24 <= day <= 30:
                suffix = "th"
            else:
                suffix = ["st", "nd", "rd"][day % 10 - 1] if day % 10 < 4 else "th"
            
            return date_obj.strftime(f'%-d{suffix} of %B, %Y')
        except ValueError:
            return date_str  # Return original if parsing fails

    def _create_default_meta_json(self, post_dir):
        """Create a default meta.json for legacy posts"""
        try:
            # Extract post date from directory name format YYYYMMDD_title
            dir_name = post_dir.name
            date_match = re.match(r'^(\d{8})_(.+)$', dir_name)
            
            if date_match:
                date_str = date_match.group(1)
                title = date_match.group(2).replace('_', ' ').title()
                
                # Format date as YYYY-MM-DD
                formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                
                # Create default meta.json
                meta_data = {
                    "title": title,
                    "date": formatted_date,
                    "tags": ["legacy"],
                    "snippet": "No preview available for this legacy post."
                }
                
                # Save meta.json
                meta_file = post_dir / "meta.json"
                with open(meta_file, 'w', encoding='utf-8') as f:
                    json.dump(meta_data, f, indent=2)
                
                print(f"Created default meta.json for {post_dir}")
                return meta_data
                
            return None
        except Exception as e:
            print(f"Error creating default meta.json for {post_dir}: {e}")
            return None

    def _collect_post_data(self):
        """Collect data from all posts with meta.json files"""
        posts = []
        
        # Walk through all directories in posts_dir
        for post_dir in self.posts_dir.glob('*/'):
            meta_file = post_dir / 'meta.json'
            post_html = post_dir / 'post.html'
            
            # Skip directories without post.html
            if not post_html.exists():
                continue
                
            # If meta.json doesn't exist but post.html does, create a default meta.json
            if not meta_file.exists():
                meta_data = self._create_default_meta_json(post_dir)
                if not meta_data:
                    continue
            else:
                # Read existing meta.json
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta_data = json.load(f)
                except Exception as e:
                    print(f"Error reading {meta_file}: {e}")
                    continue
            
            # Extract needed information
            post_data = {
                'title': meta_data.get('title', 'Untitled'),
                'date': meta_data.get('date', ''),
                'tags': meta_data.get('tags', []),
                'snippet': meta_data.get('snippet', ''),
                'path': post_dir.name,  # Just the directory name for the URL hash
                'url': f"/{post_dir.relative_to(self.base_dir)}/post.html"
            }
            
            posts.append(post_data)
        
        # Sort posts by date, most recent first
        return sorted(posts, key=lambda p: p['date'], reverse=True)

    def _generate_index_content(self, posts, title="All Posts"):
        """Generate the HTML content for an index page"""
        items_html = ""
        
        for post in posts:
            # Format date
            date_formatted = self._format_date(post['date'])
            
            # Format tags
            tags_str = ", ".join(tag.title() for tag in post['tags']) if post['tags'] else "Uncategorized"
            
            # Format item HTML with HTMX attributes
            item_html = self.index_item_template.format(
                date_formatted=date_formatted,
                tags=tags_str,
                post_url=post['url'],
                post_path=post['path'],  # Used for the URL hash
                title=post['title'],
                snippet=post['snippet']
            )
            
            items_html += item_html
        
        # Generate complete index HTML
        return self.index_template.format(
            title=title,
            items=items_html
        )

    def generate_all_indexes(self):
        """Generate all index files"""
        print("Generating indexes...")
        
        # Collect all post data
        posts = self._collect_post_data()
        
        if not posts:
            print("No posts found with meta.json data.")
            return
        
        # Generate index for all posts
        all_posts_html = self._generate_index_content(posts, title="Latest")
        with open(self.indexes_dir / 'index-all.html', 'w', encoding='utf-8') as f:
            f.write(all_posts_html)
        
        # Group posts by tag
        posts_by_tag = defaultdict(list)
        for post in posts:
            for tag in post['tags']:
                posts_by_tag[tag].append(post)
        
        # Generate index for each tag
        for tag, tag_posts in posts_by_tag.items():
            tag_html = self._generate_index_content(tag_posts, title=f"{tag.title()} Posts")
            with open(self.indexes_dir / f'index-{tag}.html', 'w', encoding='utf-8') as f:
                f.write(tag_html)
        
        print(f"Generated {len(posts_by_tag) + 1} index files.")

if __name__ == "__main__":
    generator = IndexGenerator()
    generator.generate_all_indexes()