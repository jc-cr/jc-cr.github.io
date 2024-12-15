# registry_updater.py
import sqlite3
from pathlib import Path
from datetime import datetime
import yaml
from contextlib import contextmanager
from typing import List, Dict, Any

class PostRegistry:
    def __init__(self, db_path: str = "data/posts.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def init_db(self):
        """Initialize the database with schema"""
        with self.get_db() as (conn, cur):
            cur.executescript('''
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL CHECK(type IN ('blog', 'works')),
                    title TEXT NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT,
                    path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_posts_type_date 
                ON posts(type, date DESC);
                
                CREATE INDEX IF NOT EXISTS idx_posts_date 
                ON posts(date DESC);
            ''')

    @contextmanager
    def get_db(self):
        """Database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            yield conn, cur
        finally:
            conn.close()

    def add_post(self, post_data: Dict[str, Any]):
        """Add a new post to the registry"""
        with self.get_db() as (conn, cur):
            cur.execute('''
                INSERT INTO posts (id, type, title, date, description, path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                post_data['id'],
                post_data['type'],
                post_data['title'],
                post_data['date'],
                post_data.get('description', ''),
                post_data['path']
            ))
            conn.commit()

    def get_all_posts(self) -> List[Dict[str, Any]]:
        """Get all posts from the database"""
        with self.get_db() as (conn, cur):
            cur.execute('SELECT * FROM posts ORDER BY date DESC, created_at DESC')
            return [dict(row) for row in cur.fetchall()]

    def get_latest_posts(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get latest posts across all types"""
        with self.get_db() as (conn, cur):
            cur.execute('''
                SELECT * FROM posts 
                ORDER BY date DESC, created_at DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cur.fetchall()]

    def get_posts_by_type(self, post_type: str) -> List[Dict[str, Any]]:
        """Get all posts of a specific type"""
        with self.get_db() as (conn, cur):
            cur.execute('''
                SELECT * FROM posts 
                WHERE type = ? 
                ORDER BY date DESC, created_at DESC
            ''', (post_type,))
            return [dict(row) for row in cur.fetchall()]

    def delete_post(self, post_id: str):
        """Delete a post from the registry"""
        with self.get_db() as (conn, cur):
            cur.execute('DELETE FROM posts WHERE id = ?', (post_id,))
            conn.commit()

    def update_post(self, post_id: str, post_data: Dict[str, Any]):
        """Update an existing post"""
        with self.get_db() as (conn, cur):
            fields = ', '.join(f'{k} = ?' for k in post_data.keys())
            values = list(post_data.values()) + [datetime.now().isoformat(), post_id]
            
            cur.execute(f'''
                UPDATE posts 
                SET {fields}, updated_at = ?
                WHERE id = ?
            ''', values)
            conn.commit()