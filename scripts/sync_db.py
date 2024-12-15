# sync_db.py
import os
import re
import sqlite3
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from dataclasses import dataclass
from registry_updater import PostRegistry
from update_posts import PostGenerator

@dataclass
class PostInfo:
    id: str
    type: str
    title: str
    date: str
    path: str
    description: Optional[str] = None

class DatabaseSyncService:
    def __init__(self, base_dir: str = None):
        # Use provided base_dir or default to current directory
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        
        # Set up paths relative to base directory
        self.webpage_dir = self.base_dir / 'webpage'
        self.db_path = self.base_dir / 'data' / 'posts.db'
        
        self.registry = PostRegistry(str(self.db_path))
        self.valid_types = ['blog', 'works']
        
        # Initialize PostGenerator
        self.post_generator = PostGenerator()
        self.post_generator.output_dir = self.webpage_dir
        self.post_generator.template_dir = self.base_dir / 'templates'

    def extract_post_info(self, html_path: Path) -> Optional[PostInfo]:
        """Extract post information from HTML file"""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')

            # Extract post type from path
            post_type = html_path.parent.parent.name
            if post_type not in self.valid_types:
                return None

            # Extract post ID (directory name)
            post_id = html_path.parent.name

            # Extract title and date
            article = soup.find('article')
            if not article:
                print(f"Warning: No article tag found in {html_path}")
                return None
                
            title_elem = article.find('h1')
            if not title_elem:
                print(f"Warning: No title found in {html_path}")
                return None
                
            time_elem = article.find('time')
            if not time_elem:
                print(f"Warning: No date found in {html_path}")
                return None

            title = title_elem.text.strip()
            date = time_elem.get('datetime')

            # Extract path relative to post type directory
            rel_path = html_path.parent.relative_to(self.webpage_dir / post_type)

            return PostInfo(
                id=post_id,
                type=post_type,
                title=title,
                date=date,
                path=str(rel_path),
            )
        except Exception as e:
            print(f"Error processing {html_path}: {e}")
            return None

    def scan_posts(self) -> List[PostInfo]:
        """Scan webpage directory for posts"""
        posts = []
        for post_type in self.valid_types:
            type_dir = self.webpage_dir / post_type
            if not type_dir.exists():
                continue

            # Scan each post directory
            for post_dir in type_dir.iterdir():
                if not post_dir.is_dir():
                    continue

                post_html = post_dir / 'post.html'
                if not post_html.exists():
                    continue

                post_info = self.extract_post_info(post_html)
                if post_info:
                    posts.append(post_info)

        return posts

    def regenerate_html_files(self):
        """Regenerate index.html and section pages"""
        try:
            # Generate index.html
            self.post_generator._generate_index_html()
            print("Generated index.html")

            # Generate section pages
            self.post_generator._generate_section_html()
            print("Generated section pages (blog/posts.html, works/posts.html)")

        except Exception as e:
            print(f"Error regenerating HTML files: {e}")
            raise

    def sync_database(self):
        """Synchronize database with filesystem"""
        try:
            # Ensure data directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get existing posts from database
            existing_posts = {
                post['id']: post 
                for post in self.registry.get_all_posts()
            }

            # Scan filesystem for posts
            current_posts = {
                post.id: post 
                for post in self.scan_posts()
            }

            # Find posts to add, update, and remove
            to_add = set(current_posts.keys()) - set(existing_posts.keys())
            to_update = set(current_posts.keys()) & set(existing_posts.keys())
            to_remove = set(existing_posts.keys()) - set(current_posts.keys())

            # Add new posts
            for post_id in to_add:
                post = current_posts[post_id]
                self.registry.add_post(vars(post))
                print(f"Added post: {post.title}")

            # Update existing posts
            for post_id in to_update:
                post = current_posts[post_id]
                self.registry.update_post(post_id, vars(post))
                print(f"Updated post: {post.title}")

            # Remove deleted posts
            for post_id in to_remove:
                self.registry.delete_post(post_id)
                print(f"Removed post: {existing_posts[post_id]['title']}")

            print(f"\nSync complete. Added: {len(to_add)}, Updated: {len(to_update)}, Removed: {len(to_remove)}")

            # Regenerate HTML files after database sync
            if to_add or to_update or to_remove:
                print("\nRegenerating HTML files...")
                self.regenerate_html_files()
            else:
                print("\nNo changes detected, skipping HTML regeneration")

        except Exception as e:
            print(f"Error syncing database: {e}")
            raise

def main():
    sync_service = DatabaseSyncService()
    sync_service.sync_database()

if __name__ == '__main__':
    main()
