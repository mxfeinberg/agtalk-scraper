"""
HTML parser for AgTalk forum structure.
"""

import logging
import re
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

class AgTalkParser:
    """Parser for AgTalk forum HTML structure."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_post_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract post URLs from forum page."""
        post_urls = []
        
        try:
            # Look for links to individual posts/topics
            # AgTalk typically uses topic-view.asp for individual posts
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = str(link.get('href', ''))
                
                # Look for thread view links (AgTalk uses thread-view.asp)
                if 'thread-view.asp' in href and 'tid=' in href:
                    # Extract just the tid parameter and build clean URL with flat display
                    tid_match = re.search(r'tid=(\d+)', href)
                    if tid_match:
                        tid = tid_match.group(1)
                        clean_url = f"{base_url}/forums/thread-view.asp?tid={tid}&DisplayType=flat"
                        if clean_url not in post_urls:
                            post_urls.append(clean_url)
                
                # Also look for other post patterns
                elif 'topic-view.asp' in href or 'reply-view.asp' in href:
                    full_url = urljoin(base_url, href)
                    if full_url not in post_urls:
                        post_urls.append(full_url)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in post_urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            self.logger.debug(f"Extracted {len(unique_urls)} unique post URLs")
            return unique_urls
            
        except Exception as e:
            self.logger.error(f"Error extracting post URLs: {str(e)}")
            return []
    
    def extract_post_data(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract all post data from thread page (flat display shows all posts)."""
        posts = []
        
        try:
            # Extract thread ID from URL for all posts
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            thread_id = query_params.get('tid', [''])[0]
            
            # Get the main thread title from page title
            main_title = ""
            title_elem = soup.find('title')
            if title_elem:
                raw_title = self.clean_text(title_elem.get_text())
                if raw_title.startswith('Viewing a thread - '):
                    main_title = raw_title[19:]
                else:
                    main_title = raw_title
            
            # Find all messageheader elements which indicate individual posts in flat display
            message_headers = soup.find_all('td', class_='messageheader')
            
            for i, header in enumerate(message_headers):
                # Skip if this is not a post header (some headers are for navigation)
                author_link = header.find('a', href=lambda x: x and 'view-profile.asp' in x)
                if not author_link:
                    continue
                    
                post_data = {
                    'url': f"{url}#post{i+1}",
                    'title': main_title,
                    'author': '',
                    'post_date': '',
                    'content': '',
                    'thread_id': thread_id,
                    'post_number': len(posts) + 1  # Use posts array length for correct numbering
                }
                
                # Extract author from the profile link
                post_data['author'] = self.clean_text(author_link.get_text())
                
                # Extract post date from smalltext in the header
                # Look for date in the format "Posted MM/DD/YYYY HH:MM"
                date_elem = header.find('span', class_='smalltext')
                if date_elem:
                    date_text = self.clean_text(date_elem.get_text())
                    # Extract date from "Posted MM/DD/YYYY HH:MM" format
                    date_match = re.search(r'Posted\s+(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})', date_text)
                    if date_match:
                        post_data['post_date'] = date_match.group(1)
                
                # If no date found in current header, look in the parent row structure
                if not post_data['post_date']:
                    current_row = header.find_parent('tr')
                    if current_row:
                        # Look for smalltext in the same row or adjacent rows
                        all_smalltext = current_row.find_all('span', class_='smalltext')
                        for st in all_smalltext:
                            st_text = self.clean_text(st.get_text())
                            date_match = re.search(r'Posted\s+(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})', st_text)
                            if date_match:
                                post_data['post_date'] = date_match.group(1)
                                break
                
                # Find the corresponding messagemiddle content for this post
                # Look for the next table row with messagemiddle class
                current_row = header.find_parent('tr')
                if current_row:
                    next_row = current_row.find_next_sibling('tr')
                    if next_row:
                        content_cells = next_row.find_all('td', class_='messagemiddle')
                        if len(content_cells) >= 2:
                            # Second cell contains the actual post content
                            post_data['content'] = self.clean_text(content_cells[1].get_text())
                
                # Format content consistently
                if not post_data['content'] or len(post_data['content'].strip()) < 10:
                    if post_data['title']:
                        post_data['content'] = f"Subject: {post_data['title']}, Post: [No additional content]"
                    else:
                        continue  # Skip posts with no title or content
                else:
                    subject = post_data['title'] if post_data['title'] else "[No subject]"
                    original_content = post_data['content']
                    post_data['content'] = f"Subject: {subject}, Post: {original_content}"
                
                posts.append(post_data)
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Error extracting post data from {url}: {str(e)}")
            return []
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common forum artifacts
        text = re.sub(r'(Quote:|Reply:|Originally posted by:)', '', text, flags=re.IGNORECASE)
        
        # Remove excessive punctuation
        text = re.sub(r'([.!?]){3,}', r'\1\1\1', text)
        
        # Remove URLs if they're standalone
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        return text.strip()
