#!/usr/bin/env python3
"""
AgTalk Forum Scraper
A respectful web scraper for extracting forum posts from AgTalk.
"""

import argparse
import logging
import sys
import time
from scraper import AgTalkScraper
from database import DatabaseManager
from config import ScraperConfig

def setup_logging(log_level='INFO', disable_file_logging=False):
    """Setup logging configuration."""
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if not disable_file_logging:
        handlers.append(logging.FileHandler('agtalk_scraper.log'))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def main():
    """Main entry point for the scraper."""
    parser = argparse.ArgumentParser(description='AgTalk Forum Scraper')
    parser.add_argument('--forum-id', type=int, default=3, 
                       help='Forum ID to scrape (default: 3)')
    parser.add_argument('--max-pages', type=int, default=10,
                       help='Maximum number of pages to scrape (default: 10)')
    parser.add_argument('--start-page', type=int, default=1,
                       help='Page number to start scraping from (default: 1)')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='Delay between requests in seconds (default: 2.0)')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    parser.add_argument('--reset-db', action='store_true',
                       help='Reset the database before scraping')
    parser.add_argument('--no-file-logging', action='store_true',
                       help='Disable logging to file (stdout only)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.no_file_logging)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize configuration
        config = ScraperConfig(
            base_url='https://talk.newagtalk.com',
            forum_id=args.forum_id,
            request_delay=args.delay,
            max_pages=args.max_pages,
            start_page=args.start_page
        )
        
        # Initialize database
        db_manager = DatabaseManager(config)
        
        if args.reset_db:
            logger.info("Resetting database...")
            db_manager.reset_database()
        
        # Initialize scraper
        scraper = AgTalkScraper(config, db_manager)
        
        # Check robots.txt compliance
        if not scraper.check_robots_compliance():
            logger.error("Scraping not allowed by robots.txt")
            sys.exit(1)
        
        logger.info(f"Starting scrape of forum {args.forum_id}")
        logger.info(f"Pages {args.start_page}-{args.start_page + args.max_pages - 1}, Delay: {args.delay}s")
        
        # Start scraping
        scraped_count = scraper.scrape_forum()
        
        logger.info(f"Scraping completed. Total posts scraped: {scraped_count}")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
