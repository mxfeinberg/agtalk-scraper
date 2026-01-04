"""
Database manager for storing AgTalk forum posts using PostgreSQL.
"""

import psycopg2
import psycopg2.extras
import logging
from datetime import datetime
from typing import Dict, Optional
from config import ScraperConfig

class DatabaseManager:
    """Manages PostgreSQL database operations for forum posts."""
    
    def __init__(self, config: ScraperConfig):
        """Initialize database manager with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def _get_connection(self):
        """Get database connection."""
        try:
            if self.config.database_url:
                self.logger.debug(f"Connecting to database using DATABASE_URL")
                return psycopg2.connect(self.config.database_url)
            else:
                self.logger.debug(f"Connecting to database: {self.config.db_host}:{self.config.db_port}/{self.config.db_name} as {self.config.db_user}")
                return psycopg2.connect(
                    host=self.config.db_host,
                    port=self.config.db_port,
                    database=self.config.db_name,
                    user=self.config.db_user,
                    password=self.config.db_password
                )
        except psycopg2.Error as e:
            self.logger.error(f"Database connection failed: {str(e)}")
            self.logger.error(f"Connection details - Host: {self.config.db_host}, Port: {self.config.db_port}, DB: {self.config.db_name}, User: {self.config.db_user}")
            raise
    
    def init_database(self):
        """Initialize the database with required tables."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create posts table
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS posts (
                            id SERIAL PRIMARY KEY,
                            url TEXT UNIQUE NOT NULL,
                            title TEXT NOT NULL,
                            author TEXT,
                            post_date TIMESTAMP WITHOUT TIME ZONE,
                            content TEXT NOT NULL,
                            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            thread_id TEXT,
                            post_number INTEGER
                        )
                    ''')
                    
                    # Create indexes for faster lookups
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_url ON posts(url)
                    ''')
                    
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_thread_id ON posts(thread_id)
                    ''')
                    
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_scraped_at ON posts(scraped_at)
                    ''')
                    
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_posts_post_date ON posts(post_date)
                    ''')
                    
                    conn.commit()
                    self.logger.info("Database initialized successfully")
                    
        except psycopg2.Error as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    def post_exists(self, url: str) -> bool:
        """Check if a post with the given URL already exists."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM posts WHERE url = %s", (url,))
                    return cursor.fetchone() is not None
        except psycopg2.Error as e:
            self.logger.error(f"Error checking post existence: {str(e)}")
            return False
    
    def save_post(self, post_data: Dict) -> bool:
        """Save a post to the database."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Convert post_date string to timestamp if provided
                    post_timestamp = None
                    if post_data.get('post_date'):
                        try:
                            # Parse MM/DD/YYYY HH:MM format to timestamp
                            from datetime import datetime
                            post_timestamp = datetime.strptime(post_data['post_date'], '%m/%d/%Y %H:%M')
                        except ValueError:
                            self.logger.warning(f"Could not parse date: {post_data.get('post_date')}")
                    
                    # Insert post data with ON CONFLICT handling
                    cursor.execute('''
                        INSERT INTO posts 
                        (url, title, author, post_date, content, thread_id, post_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO UPDATE SET
                            title = EXCLUDED.title,
                            author = EXCLUDED.author,
                            post_date = EXCLUDED.post_date,
                            content = EXCLUDED.content,
                            thread_id = EXCLUDED.thread_id,
                            post_number = EXCLUDED.post_number,
                            scraped_at = CURRENT_TIMESTAMP
                    ''', (
                        post_data['url'],
                        post_data['title'],
                        post_data.get('author', ''),
                        post_timestamp,
                        post_data['content'],
                        post_data.get('thread_id', ''),
                        post_data.get('post_number', 0)
                    ))
                    
                    rows_affected = cursor.rowcount
                    conn.commit()
                    
                    if rows_affected > 0:
                        self.logger.debug(f"Saved post: {post_data['title'][:50]}... (rows affected: {rows_affected})")
                        return True
                    else:
                        self.logger.warning(f"No rows affected when saving post: {post_data['url']}")
                        return False
                    
        except psycopg2.Error as e:
            self.logger.error(f"PostgreSQL error saving post: {str(e)}")
            self.logger.error(f"Post data: url={post_data.get('url', 'N/A')}, title={post_data.get('title', 'N/A')[:50]}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error saving post: {str(e)}")
            self.logger.error(f"Post data: url={post_data.get('url', 'N/A')}, title={post_data.get('title', 'N/A')[:50]}")
            return False
    
    def get_post_count(self) -> int:
        """Get the total number of posts in the database."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM posts")
                    return cursor.fetchone()[0]
        except psycopg2.Error as e:
            self.logger.error(f"Error getting post count: {str(e)}")
            return 0
    
    def get_posts_by_thread(self, thread_id: str) -> list:
        """Get all posts for a specific thread."""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute('''
                        SELECT * FROM posts 
                        WHERE thread_id = %s 
                        ORDER BY post_number
                    ''', (thread_id,))
                    
                    return [dict(row) for row in cursor.fetchall()]
                    
        except psycopg2.Error as e:
            self.logger.error(f"Error getting posts by thread: {str(e)}")
            return []
    
    def search_posts(self, search_term: str) -> list:
        """Search posts by content or title."""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute('''
                        SELECT * FROM posts 
                        WHERE title ILIKE %s OR content ILIKE %s
                        ORDER BY scraped_at DESC
                    ''', (f'%{search_term}%', f'%{search_term}%'))
                    
                    return [dict(row) for row in cursor.fetchall()]
                    
        except psycopg2.Error as e:
            self.logger.error(f"Error searching posts: {str(e)}")
            return []
    
    def reset_database(self):
        """Reset the database by dropping and recreating tables."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DROP TABLE IF EXISTS posts")
                    conn.commit()
            
            self.init_database()
            self.logger.info("Database reset successfully")
            
        except psycopg2.Error as e:
            self.logger.error(f"Database reset failed: {str(e)}")
            raise
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    
                    # Total posts
                    cursor.execute("SELECT COUNT(*) FROM posts")
                    total_posts = cursor.fetchone()[0]
                    
                    # Unique authors
                    cursor.execute("SELECT COUNT(DISTINCT author) FROM posts WHERE author IS NOT NULL AND author != ''")
                    unique_authors = cursor.fetchone()[0]
                    
                    # Date range
                    cursor.execute("SELECT MIN(post_date), MAX(post_date) FROM posts WHERE post_date IS NOT NULL")
                    date_range = cursor.fetchone()
                    
                    # Unique threads
                    cursor.execute("SELECT COUNT(DISTINCT thread_id) FROM posts WHERE thread_id IS NOT NULL AND thread_id != ''")
                    unique_threads = cursor.fetchone()[0]
                    
                    return {
                        'total_posts': total_posts,
                        'unique_authors': unique_authors,
                        'unique_threads': unique_threads,
                        'earliest_post': date_range[0] if date_range[0] else 'N/A',
                        'latest_post': date_range[1] if date_range[1] else 'N/A'
                    }
                    
        except psycopg2.Error as e:
            self.logger.error(f"Error getting database stats: {str(e)}")
            return {}