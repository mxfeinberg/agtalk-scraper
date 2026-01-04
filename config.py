"""
Configuration settings for the AgTalk scraper.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScraperConfig:
    """Configuration class for the scraper."""
    base_url: str = 'https://talk.newagtalk.com'
    forum_id: int = 3
    request_delay: float = 20.0
    max_pages: int = 100
    start_page: int = 1
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 5.0

    # Database settings
    db_host: str = os.environ.get('PGHOST', 'localhost')
    db_port: int = int(os.environ.get('PGPORT', '5432'))
    db_name: str = os.environ.get('PGDATABASE', 'agtalk')
    db_user: str = os.environ.get('PGUSER', 'postgres')
    db_password: str = os.environ.get('PGPASSWORD', 'postgres')
    database_url: str = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/agtalk?sslmode=prefer')

    # Parsing settings
    min_content_length: int = 10
    max_title_length: int = 200

    # User agent
    user_agent: str = 'AgTalk-Respectful-Scraper/1.0 (Educational Purpose)'

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.request_delay < 1.0:
            raise ValueError("Request delay must be at least 1.0 second")

        if self.max_pages < 1:
            raise ValueError("Max pages must be at least 1")

        if self.start_page < 1:
            raise ValueError("Start page must be at least 1")

        if self.forum_id < 1:
            raise ValueError("Forum ID must be positive")

        if not self.base_url.startswith(('http://', 'https://')):
            raise ValueError("Base URL must start with http:// or https://")
