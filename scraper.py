"""
Main scraper class for AgTalk forum.
"""

import logging
import re
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from robots_checker import RobotsChecker
from parser import AgTalkParser
from database import DatabaseManager
from config import ScraperConfig

class AgTalkScraper:
    """Main scraper class for AgTalk forum."""
    
    def __init__(self, config: ScraperConfig, db_manager: DatabaseManager):
        self.config = config
        self.db_manager = db_manager
        self.parser = AgTalkParser()
        self.robots_checker = RobotsChecker(config.base_url)
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
        # Set user agent
        self.session.headers.update({
            'User-Agent': 'AgTalk-Respectful-Scraper/1.0 (Educational Purpose)'
        })
    
    def check_robots_compliance(self) -> bool:
        """Check if scraping is allowed by robots.txt."""
        return self.robots_checker.can_fetch()
    
    def make_request(self, url: str) -> requests.Response:
        """Make a respectful HTTP request with error handling."""
        try:
            self.logger.debug(f"Requesting: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Respectful delay
            time.sleep(self.config.request_delay)
            
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {str(e)}")
            raise
    
    def get_forum_page_url(self, forum_id: int, page: int) -> str:
        """Build URL for a specific forum and page number.

        Args:
            forum_id: The forum ID to build URL for
            page: The page number (1-indexed)

        Returns:
            The full URL for the forum page
        """
        if page == 1:
            return f"{self.config.base_url}/forums/forum-view.asp?fid={forum_id}&displaytype=flat"
        else:
            bookmark = 1 + ((page - 1) * 50)
            return f"{self.config.base_url}/forums/forum-view.asp?fid={forum_id}&bookmark={bookmark}&displaytype=flat"

    def get_forum_page_urls(self) -> list:
        """Get all forum page URLs to scrape."""
        urls = []
        page = self.config.start_page
        end_page = self.config.start_page + self.config.max_pages - 1

        while page <= end_page:
            urls.append(self.get_forum_page_url(self.config.forum_id, page))
            page += 1

        return urls
    
    def scrape_forum_page(self, url: str) -> list:
        """Scrape a single forum page and return post URLs."""
        try:
            response = self.make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            post_urls = self.parser.extract_post_urls(soup, self.config.base_url)
            self.logger.info(f"Found {len(post_urls)} posts on page: {url}")
            
            return post_urls
        except Exception as e:
            self.logger.error(f"Failed to scrape forum page {url}: {str(e)}")
            return []
    
    def scrape_post(self, post_url: str) -> list:
        """Scrape all posts from a thread and return list of post data."""
        all_posts_data = []
        page = 1
        
        # Extract thread ID from URL for pagination
        thread_match = re.search(r'tid=(\d+)', post_url)
        if not thread_match:
            self.logger.error(f"Could not extract thread ID from URL: {post_url}")
            return []
        
        thread_id = thread_match.group(1)
        
        while True:
            try:
                # Build URL for current page
                if page == 1:
                    current_url = f"{self.config.base_url}/forums/thread-view.asp?tid={thread_id}&DisplayType=flat"
                else:
                    start = 1 + ((page - 1) * 50)
                    current_url = f"{self.config.base_url}/forums/thread-view.asp?tid={thread_id}&start={start}&displaytype=flat"
                
                response = self.make_request(current_url)
                soup = BeautifulSoup(response.content, 'html.parser')

                posts_data = self.parser.extract_post_data(soup, current_url, self.config.forum_id)
                
                if not posts_data:
                    # No posts found on this page, we've reached the end
                    break
                
                all_posts_data.extend(posts_data)
                self.logger.debug(f"Scraped {len(posts_data)} posts from thread page {page}: {current_url}")
                
                # Check if there are pagination links indicating more pages
                # Look for links with start= parameter that have a higher start value
                next_page_exists = False
                next_start = 1 + (page * 50)
                
                # Check for pagination links
                nav_links = soup.find_all('a', href=re.compile(r'start=\d+'))
                for link in nav_links:
                    href = link.get('href', '') or ''
                    start_match = re.search(r'start=(\d+)', str(href))
                    if start_match:
                        start_value = int(start_match.group(1))
                        if start_value >= next_start:
                            next_page_exists = True
                            break
                
                if not next_page_exists:
                    break
                
                page += 1
                
            except Exception as e:
                self.logger.error(f"Failed to scrape thread page {page} for {thread_id}: {str(e)}")
                break
        
        if all_posts_data:
            self.logger.debug(f"Total scraped {len(all_posts_data)} posts from thread {thread_id}")
        else:
            self.logger.warning(f"No post data extracted from thread: {thread_id}")
        
        return all_posts_data
    
    def scrape_forum(self) -> int:
        """Main scraping method."""
        total_scraped = 0
        
        # Get all forum page URLs
        forum_urls = self.get_forum_page_urls()
        self.logger.info(f"Will scrape {len(forum_urls)} forum pages")
        
        for forum_url in forum_urls:
            try:
                # Get post URLs from forum page
                post_urls = self.scrape_forum_page(forum_url)
                
                for post_url in post_urls:
                    # Check if thread already exists in database
                    if self.db_manager.post_exists(post_url):
                        self.logger.debug(f"Thread already exists, skipping: {post_url}")
                        continue
                    
                    # Scrape all posts from thread
                    posts_data = self.scrape_post(post_url)
                    
                    if posts_data:
                        # Save each post to database
                        for post_data in posts_data:
                            # Create unique URL for each post in thread
                            unique_url = f"{post_url}#post{post_data['post_number']}"
                            post_data['url'] = unique_url
                            
                            # Check if this specific post already exists
                            if not self.db_manager.post_exists(unique_url):
                                self.db_manager.save_post(post_data)
                                total_scraped += 1
                        
                        if total_scraped % 10 == 0:
                            self.logger.info(f"Progress: {total_scraped} posts scraped")
                
            except Exception as e:
                self.logger.error(f"Error processing forum page {forum_url}: {str(e)}")
                continue
        
        return total_scraped
