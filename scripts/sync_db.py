# sync_db.py
import os
import re
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from dataclasses import dataclass
from registry_updater import PostRegistry

from argparse import ArgumentParser

@dataclass
class PostInfo:
    id: str
    type: str
    title: str
    date: str
    path: str
    content_hash: str
    description: Optional[str] = None

class DatabaseSyncService:
    def __init__(self, base_dir: str = None):
        # Use provided base_dir or default to current directory
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        
        # Set up paths relative to base directory
        self.webpage_dir = self.base_dir / 'webpage'
        self.db_path = self.base_dir / 'data' / 'posts.db'
        self.template_dir = self.base_dir / 'templates'
        
        self.registry = PostRegistry(str(self.db_path))
        self.valid_types = ['blog', 'works']
        
        # Ensure the content_hash column exists
        self._ensure_content_hash_column()
    
    def _ensure_content_hash_column(self):
        """Ensure the content_hash column exists in the posts table"""
        with self.registry.get_db() as (conn, cur):
            # Check if column exists
            cur.execute("PRAGMA table_info(posts)")
            columns = {col[1] for col in cur.fetchall()}
            
            if 'content_hash' not in columns:
                cur.execute('''
                    ALTER TABLE posts 
                    ADD COLUMN content_hash TEXT
                ''')
                conn.commit()

    def _compute_hash(self, html_path: Path) -> str:
        """Compute hash of file content"""
        with open(html_path, 'rb') as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest()

    def extract_post_info(self, html_path: Path) -> Optional[PostInfo]:
        """Extract post information from HTML file"""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')

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

            # Compute content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            try:
                date_obj = datetime.strptime(time_elem.get('datetime'), '%Y-%m-%d')
            except ValueError:
                print(f"Warning: Invalid date format in {html_path}")
                date_obj = datetime.now()
                
            normalized_date = date_obj.strftime('%Y-%m-%d')  # This ensures format like 2024-12-08
            
            return PostInfo(
                id=post_id,
                type=post_type,
                title=title,
                date=normalized_date,
                path=str(rel_path),
                content_hash=content_hash
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

    def _replace_template_vars(self, template: str, variables: dict) -> str:
        """Replace all template variables with their values"""
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{ {key} }}}}"
            result = result.replace(placeholder, str(value))
        return result

    def regenerate_html_files(self):
        """Regenerate index.html and section pages"""
        try:
            # Generate index.html
            with open(self.template_dir / 'index_template.html', 'r', encoding='utf-8') as f:
                template = f.read()
            
            latest_posts = self.registry.get_latest_posts(5)
            posts_html = ''
            for post in latest_posts:
                post_url = f"/webpage/{post['type']}/{post['path']}/post.html"
                posts_html += f'<li><a href="{post_url}">{post["title"]}</a> ({post["date"]})</li>\n'
            
            index_html = self._replace_template_vars(template, {'latest_posts': posts_html})
            with open(self.base_dir / 'index.html', 'w', encoding='utf-8') as f:
                f.write(index_html)
            print("Generated index.html")

            # Generate section pages
            with open(self.template_dir / 'section_template.html', 'r', encoding='utf-8') as f:
                template = f.read()
            
            for section in self.valid_types:
                posts = self.registry.get_posts_by_type(section)
                posts_html = ''
                for post in posts:
                    post_url = f"{post['path']}/post.html"
                    posts_html += f'<li><a href="{post_url}">{post["title"]}</a> ({post["date"]})</li>\n'
                
                section_html = self._replace_template_vars(template, {
                    'posts': posts_html,
                    'section': section.title()
                })
                
                section_dir = self.webpage_dir / section
                section_dir.mkdir(exist_ok=True)
                with open(section_dir / 'posts.html', 'w', encoding='utf-8') as f:
                    f.write(section_html)
            print("Generated section pages")

        except Exception as e:
            print(f"Error regenerating HTML files: {e}")
            raise

    def sync_database(self, force_regenerate: bool = False):
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
            to_update = set()
            
            # Check which posts actually need updating
            for post_id in set(current_posts.keys()) & set(existing_posts.keys()):
                current_post = current_posts[post_id]
                existing_post = existing_posts[post_id]
                
                # Compare content hashes
                if (not existing_post.get('content_hash') or 
                    current_post.content_hash != existing_post['content_hash']):
                    to_update.add(post_id)
            
            to_remove = set(existing_posts.keys()) - set(current_posts.keys())

            # Add new posts
            for post_id in to_add:
                post = current_posts[post_id]
                self.registry.add_post(vars(post))
                print(f"Added post: {post.title}")

            # Update modified posts
            for post_id in to_update:
                post = current_posts[post_id]
                self.registry.update_post(post_id, vars(post))
                print(f"Updated post: {post.title}")

            # Remove deleted posts
            for post_id in to_remove:
                self.registry.delete_post(post_id)
                print(f"Removed post: {existing_posts[post_id]['title']}")

            print(f"\nSync complete. Added: {len(to_add)}, Updated: {len(to_update)}, Removed: {len(to_remove)}")

            # Add force regeneration
            if force_regenerate:
                print("\nForce regenerating HTML files...")
                self.regenerate_html_files()
            elif to_add or to_update or to_remove:
                print("\nRegenerating HTML files...")
                self.regenerate_html_files()
            else:
                print("\nNo changes detected, skipping HTML regeneration")

        except Exception as e:
            print(f"Error syncing database: {e}")
            raise

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--force-regenerate', action='store_true', help='Force regeneration of HTML files')

    args = parser.parse_args()

    sync_service = DatabaseSyncService()
    sync_service.sync_database(args.force_regenerate)