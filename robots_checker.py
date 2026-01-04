"""
Robots.txt compliance checker.
"""

import logging
import urllib.robotparser
from urllib.parse import urljoin

class RobotsChecker:
    """Checks robots.txt compliance for web scraping."""
    
    def __init__(self, base_url: str, user_agent: str = 'AgTalk-Respectful-Scraper'):
        self.base_url = base_url
        self.user_agent = user_agent
        self.logger = logging.getLogger(__name__)
        self.robots_parser = None
        self._load_robots_txt()
    
    def _load_robots_txt(self):
        """Load and parse robots.txt file."""
        try:
            robots_url = urljoin(self.base_url, '/robots.txt')
            self.robots_parser = urllib.robotparser.RobotFileParser()
            self.robots_parser.set_url(robots_url)
            self.robots_parser.read()
            self.logger.info(f"Loaded robots.txt from: {robots_url}")
            
        except Exception as e:
            self.logger.warning(f"Could not load robots.txt: {str(e)}")
            self.logger.info("Proceeding with conservative approach")
            self.robots_parser = None
    
    def can_fetch(self, url_path: str = '/forums/') -> bool:
        """Check if the given URL path can be fetched according to robots.txt."""
        if self.robots_parser is None:
            # If we can't load robots.txt, be conservative but allow scraping
            # with proper rate limiting
            self.logger.info("No robots.txt available, proceeding with respectful scraping")
            return True
        
        try:
            full_url = urljoin(self.base_url, url_path)
            can_fetch = self.robots_parser.can_fetch(self.user_agent, full_url)
            
            if can_fetch:
                self.logger.info(f"Scraping allowed for: {url_path}")
            else:
                self.logger.warning(f"Scraping NOT allowed for: {url_path}")
            
            return can_fetch
            
        except Exception as e:
            self.logger.error(f"Error checking robots.txt for {url_path}: {str(e)}")
            # Default to not allowed if there's an error
            return False
    
    def get_crawl_delay(self) -> float:
        """Get the crawl delay specified in robots.txt."""
        if self.robots_parser is None:
            # Default conservative delay
            return 2.0
        
        try:
            delay = self.robots_parser.crawl_delay(self.user_agent)
            if delay is not None:
                self.logger.info(f"Robots.txt specifies crawl delay: {delay} seconds")
                return float(delay)
            else:
                # Use conservative default
                return 2.0
                
        except Exception as e:
            self.logger.warning(f"Error getting crawl delay: {str(e)}")
            return 2.0
    
    def get_request_rate(self) -> tuple:
        """Get the request rate specified in robots.txt."""
        if self.robots_parser is None:
            return None, None
        
        try:
            rate = self.robots_parser.request_rate(self.user_agent)
            if rate is not None:
                self.logger.info(f"Robots.txt specifies request rate: {rate}")
                return rate
            else:
                return None, None
                
        except Exception as e:
            self.logger.warning(f"Error getting request rate: {str(e)}")
            return None, None
