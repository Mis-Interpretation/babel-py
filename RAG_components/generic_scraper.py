"""
Generic Web Scraper for Documentation Sites
Configurable scraper that can handle multiple documentation sources
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import re
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenericWebScraper:
    def __init__(self, config_file: str = "RAG_components/scraping_config.json"):
        """Initialize the scraper with configuration"""
        self.config = self._load_config(config_file)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def _load_config(self, config_file: str) -> Dict:
        """Load scraping configuration from JSON file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def discover_urls(self, source_name: str, max_pages: Optional[int] = None) -> List[str]:
        """Discover URLs from a configured source"""
        if source_name not in self.config:
            raise ValueError(f"Source '{source_name}' not found in configuration")
        
        source_config = self.config[source_name]
        discovered_urls = set()
        
        for base_url in source_config["base_urls"]:
            logger.info(f"Discovering URLs from: {base_url}")
            urls = self._crawl_site(base_url, source_config, max_pages)
            discovered_urls.update(urls)
            
        logger.info(f"Discovered {len(discovered_urls)} URLs for {source_name}")
        return list(discovered_urls)
    
    def _crawl_site(self, base_url: str, config: Dict, max_pages: Optional[int]) -> Set[str]:
        """Crawl a site to discover documentation URLs"""
        discovered = set()
        to_visit = {base_url}
        visited = set()
        
        while to_visit and (max_pages is None or len(discovered) < max_pages):
            current_url = to_visit.pop()
            if current_url in visited:
                continue
                
            visited.add(current_url)
            
            try:
                response = self.session.get(current_url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all links on the page
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(current_url, href)
                    
                    if self._should_include_url(full_url, config):
                        discovered.add(full_url)
                        
                        # Add to visit queue if it matches discovery patterns
                        if self._matches_discovery_patterns(full_url, config):
                            to_visit.add(full_url)
                
                # Rate limiting
                time.sleep(config.get("rate_limit", {}).get("delay_seconds", 0.5))
                
            except Exception as e:
                logger.warning(f"Error crawling {current_url}: {e}")
                continue
        
        return discovered
    
    def _should_include_url(self, url: str, config: Dict) -> bool:
        """Check if URL should be included based on patterns"""
        # Check exclude patterns
        for pattern in config.get("exclude_patterns", []):
            if pattern in url:
                return False
        
        # Check if URL matches any discovery pattern
        for pattern in config.get("discovery_patterns", []):
            if pattern in url:
                return True
                
        return False
    
    def _matches_discovery_patterns(self, url: str, config: Dict) -> bool:
        """Check if URL matches discovery patterns for further crawling"""
        for pattern in config.get("discovery_patterns", []):
            if pattern in url:
                return True
        return False
    
    def scrape_urls(self, urls: List[str], source_name: str) -> List[Dict]:
        """Scrape content from a list of URLs"""
        if source_name not in self.config:
            raise ValueError(f"Source '{source_name}' not found in configuration")
        
        source_config = self.config[source_name]
        max_workers = source_config.get("rate_limit", {}).get("max_concurrent", 3)
        
        scraped_docs = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scraping tasks
            future_to_url = {
                executor.submit(self._scrape_single_url, url, source_config): url 
                for url in urls
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    doc = future.result()
                    if doc and len(doc.get("text", "")) > 100:  # Filter out empty/short content
                        scraped_docs.append(doc)
                        logger.info(f"✅ Scraped: {url}")
                    else:
                        logger.warning(f"⚠️ Skipped (insufficient content): {url}")
                except Exception as e:
                    logger.error(f"❌ Error scraping {url}: {e}")
        
        logger.info(f"Successfully scraped {len(scraped_docs)} documents")
        return scraped_docs
    
    def _scrape_single_url(self, url: str, config: Dict) -> Optional[Dict]:
        """Scrape content from a single URL"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # CRITICAL FIX: Ensure proper UTF-8 encoding
            # First, try to detect encoding from response headers
            if response.encoding is None or response.encoding.lower() in ['iso-8859-1', 'ascii']:
                # If no encoding specified or default encoding, try UTF-8
                response.encoding = 'utf-8'
            
            # Get the content with proper encoding
            try:
                content = response.text
            except UnicodeDecodeError:
                # Fallback: try to decode as UTF-8 with error handling
                content = response.content.decode('utf-8', errors='replace')
            
            # Parse with BeautifulSoup, explicitly specifying UTF-8
            soup = BeautifulSoup(content, 'html.parser', from_encoding='utf-8')
            
            # Extract title
            title = self._extract_title(soup, config)
            
            # Extract main content
            content = self._extract_content(soup, config)
            
            # Extract code blocks separately
            code_blocks = self._extract_code_blocks(soup, config)
            
            # Classify content type
            content_type = self._classify_content(title, content, url)
            
            # Build document
            doc = {
                "url": url,
                "title": title,
                "text": content,
                "code_blocks": code_blocks,
                "content_type": content_type,
                "metadata": {
                    **config.get("metadata", {}),
                    "url": url,
                    "title": title,
                    "content_type": content_type,
                    "has_code": len(code_blocks) > 0,
                    "scraped_at": time.time()
                }
            }
            
            # Rate limiting
            time.sleep(config.get("rate_limit", {}).get("delay_seconds", 0.5))
            
            return doc
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup, config: Dict) -> str:
        """Extract page title using configured selectors"""
        title_selectors = config.get("content_selectors", {}).get("title", ["title", "h1"])
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title:
                    return title
        
        return "Untitled Document"
    
    def _extract_content(self, soup: BeautifulSoup, config: Dict) -> str:
        """Extract main content using configured selectors"""
        content_selectors = config.get("content_selectors", {}).get("main_content", ["main", "article", "div.content"])
        
        content_blocks = []
        
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator=" ", strip=True)
                if text and len(text) > 50:  # Only include substantial content
                    content_blocks.append(text)
        
        # If no content found with selectors, try to extract from body
        if not content_blocks:
            body = soup.find('body')
            if body:
                # Remove script and style elements
                for script in body(["script", "style", "nav", "header", "footer"]):
                    script.decompose()
                content_blocks.append(body.get_text(separator=" ", strip=True))
        
        return "\n\n".join(content_blocks)
    
    def _extract_code_blocks(self, soup: BeautifulSoup, config: Dict) -> List[str]:
        """Extract code blocks separately"""
        code_selectors = config.get("content_selectors", {}).get("code_blocks", ["pre", "code"])
        code_blocks = []
        
        for selector in code_selectors:
            elements = soup.select(selector)
            for element in elements:
                code = element.get_text(strip=True)
                if code and len(code) > 10:  # Only include substantial code
                    code_blocks.append(code)
        
        return code_blocks
    
    def _classify_content(self, title: str, content: str, url: str) -> str:
        """Classify content type based on indicators"""
        text_to_analyze = f"{title} {content} {url}".lower()
        
        classification_config = self.config.get("content_classification", {})
        
        for content_type, type_config in classification_config.items():
            indicators = type_config.get("indicators", [])
            for indicator in indicators:
                if indicator.lower() in text_to_analyze:
                    return content_type
        
        return "general"
    
    def scrape_source(self, source_name: str, max_pages: Optional[int] = None) -> List[Dict]:
        """Complete pipeline: discover and scrape a source"""
        logger.info(f"Starting scrape for source: {source_name}")
        
        # Discover URLs
        urls = self.discover_urls(source_name, max_pages)
        
        # Scrape content
        docs = self.scrape_urls(urls, source_name)
        
        logger.info(f"Completed scraping {source_name}: {len(docs)} documents")
        return docs

# Convenience function for backward compatibility with existing scraper
def scrape_unity_docs(max_pages: Optional[int] = None) -> List[Dict]:
    """Scrape Unity documentation using the generic scraper"""
    scraper = GenericWebScraper()
    return scraper.scrape_source("unity", max_pages)

if __name__ == "__main__":
    # Test the scraper
    scraper = GenericWebScraper()
    
    # Test with a small subset
    docs = scraper.scrape_source("unity", max_pages=10)
    
    print(f"Scraped {len(docs)} documents")
    if docs:
        print(f"Sample document: {docs[0]['title']}")
        print(f"Content type: {docs[0]['content_type']}")
        print(f"Has code: {docs[0]['metadata']['has_code']}")
