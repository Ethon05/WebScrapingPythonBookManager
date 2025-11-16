#!/usr/bin/env python3
"""
Book Scraper - Production-Grade Web Scraping Tool
Scrapes book data from books.toscrape.com with pagination, error handling, and export functionality.

Author: ScrapeMaster-X
Email: your.email@example.com
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import json
import logging
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BookScraper:
    """
    A production-grade web scraper for books.toscrape.com
    
    Features:
    - Automatic pagination
    - Request throttling with random delays
    - Error handling with retry logic
    - Robots.txt compliance
    - CSV and JSON export
    """
    
    def __init__(self, base_url: str = "https://books.toscrape.com/", 
                 min_records: int = 500,
                 max_retries: int = 3,
                 delay_range: tuple = (1, 2)):
        """
        Initialize the BookScraper
        
        Args:
            base_url: The base URL of the website to scrape
            min_records: Minimum number of records to collect
            max_retries: Maximum number of retries for failed requests
            delay_range: Tuple of (min_delay, max_delay) in seconds
        """
        self.base_url = base_url
        self.min_records = min_records
        self.max_retries = max_retries
        self.delay_range = delay_range
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.books_data: List[Dict] = []
        
    def check_robots_txt(self) -> bool:
        """
        Check if scraping is allowed according to robots.txt
        
        Returns:
            bool: True if scraping is allowed, False otherwise
        """
        try:
            robots_url = urljoin(self.base_url, '/robots.txt')
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            can_fetch = rp.can_fetch('*', self.base_url)
            logger.info(f"Robots.txt check: {'Allowed' if can_fetch else 'Disallowed'}")
            return can_fetch
        except Exception as e:
            logger.warning(f"Could not read robots.txt: {e}. Proceeding with caution.")
            return True
    
    def apply_throttle(self):
        """Apply random delay between requests to avoid overwhelming the server"""
        delay = random.uniform(*self.delay_range)
        logger.debug(f"Applying throttle: {delay:.2f} seconds")
        time.sleep(delay)
    
    def make_request(self, url: str, retries: int = 0) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic
        
        Args:
            url: URL to fetch
            retries: Current retry attempt number
            
        Returns:
            Response object if successful, None otherwise
        """
        try:
            self.apply_throttle()
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            logger.debug(f"Successfully fetched: {url}")
            return response
        except requests.exceptions.RequestException as e:
            if retries < self.max_retries:
                logger.warning(f"Request failed (attempt {retries + 1}/{self.max_retries}): {e}")
                time.sleep(2 ** retries)  # Exponential backoff
                return self.make_request(url, retries + 1)
            else:
                logger.error(f"Failed to fetch {url} after {self.max_retries} retries: {e}")
                return None
    
    def extract_rating(self, article) -> str:
        """
        Extract star rating from book article
        
        Args:
            article: BeautifulSoup article element
            
        Returns:
            Rating as string (e.g., "Five", "Four", "Three", etc.)
        """
        rating_element = article.find('p', class_='star-rating')
        if rating_element:
            # The rating class is like "star-rating Three"
            classes = rating_element.get('class', [])
            for cls in classes:
                if cls in ['One', 'Two', 'Three', 'Four', 'Five']:
                    return cls
        return "Unknown"
    
    def parse_book_listing(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Parse book listing page and extract book information
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of dictionaries containing book data
        """
        books = []
        articles = soup.find_all('article', class_='product_pod')
        
        for article in articles:
            try:
                # Extract title
                h3_element = article.find('h3')
                if not h3_element:
                    continue
                title_element = h3_element.find('a')
                if not title_element:
                    continue
                title = str(title_element.get('title', 'N/A'))
                
                # Extract product detail page link
                detail_link = str(title_element.get('href', ''))
                detail_url = urljoin(self.base_url, detail_link)
                
                # Extract price
                price_element = article.find('p', class_='price_color')
                price = price_element.text.strip() if price_element else 'N/A'
                
                # Extract rating
                rating = self.extract_rating(article)
                
                # Extract image URL
                image_element = article.find('img')
                image_url = urljoin(self.base_url, str(image_element.get('src', ''))) if image_element else 'N/A'
                
                # Extract stock availability
                stock_element = article.find('p', class_='instock availability')
                stock = stock_element.text.strip() if stock_element else 'Unknown'
                
                book_data = {
                    'title': title,
                    'price': price,
                    'rating': rating,
                    'stock_availability': stock,
                    'product_detail_url': detail_url,
                    'image_url': image_url
                }
                
                books.append(book_data)
                logger.debug(f"Extracted book: {title}")
                
            except Exception as e:
                logger.error(f"Error parsing book article: {e}")
                continue
        
        return books
    
    def get_next_page_url(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        Extract the URL of the next page
        
        Args:
            soup: BeautifulSoup object of current page
            current_url: URL of the current page
            
        Returns:
            URL of next page or None if no next page exists
        """
        next_button = soup.find('li', class_='next')
        if next_button:
            next_link = next_button.find('a')
            if next_link:
                next_url = str(next_link.get('href', ''))
                # Handle relative URLs
                return urljoin(current_url, next_url)
        return None
    
    def scrape(self) -> List[Dict]:
        """
        Main scraping method - iterates through pages and collects book data
        
        Returns:
            List of dictionaries containing all scraped book data
        """
        logger.info("Starting web scraping process...")
        
        # Check robots.txt compliance
        if not self.check_robots_txt():
            logger.warning("Robots.txt indicates scraping may not be allowed. Proceeding with caution.")
        
        current_url = self.base_url + "catalogue/page-1.html"
        page_num = 1
        
        while len(self.books_data) < self.min_records:
            logger.info(f"Scraping page {page_num} - URL: {current_url}")
            logger.info(f"Books collected so far: {len(self.books_data)}")
            
            # Fetch the page
            response = self.make_request(current_url)
            if not response:
                logger.error(f"Failed to fetch page {page_num}. Stopping.")
                break
            
            # Parse the page
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract book data from current page
            books_on_page = self.parse_book_listing(soup)
            self.books_data.extend(books_on_page)
            logger.info(f"Extracted {len(books_on_page)} books from page {page_num}")
            
            # Check if we've collected enough records
            if len(self.books_data) >= self.min_records:
                logger.info(f"Target reached! Collected {len(self.books_data)} books.")
                break
            
            # Find next page
            next_url = self.get_next_page_url(soup, current_url)
            if not next_url:
                logger.info("No more pages available.")
                break
            
            current_url = next_url
            page_num += 1
        
        logger.info(f"Scraping completed. Total books collected: {len(self.books_data)}")
        return self.books_data
    
    def export_to_csv(self, filename: str = "books_data.csv"):
        """
        Export scraped data to CSV file
        
        Args:
            filename: Name of the output CSV file
        """
        if not self.books_data:
            logger.warning("No data to export to CSV")
            return
        
        try:
            df = pd.DataFrame(self.books_data)
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Data exported to CSV: {filename} ({len(self.books_data)} records)")
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
    
    def export_to_json(self, filename: str = "books_data.json"):
        """
        Export scraped data to JSON file
        
        Args:
            filename: Name of the output JSON file
        """
        if not self.books_data:
            logger.warning("No data to export to JSON")
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.books_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Data exported to JSON: {filename} ({len(self.books_data)} records)")
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
    
    def print_summary(self):
        """Print a summary of the scraping results"""
        if not self.books_data:
            print("\nNo data collected.")
            return
        
        print("\n" + "="*60)
        print("SCRAPING SUMMARY")
        print("="*60)
        print(f"Total Books Scraped: {len(self.books_data)}")
        print(f"Target Records: {self.min_records}")
        print(f"Status: {'✓ SUCCESS' if len(self.books_data) >= self.min_records else '✗ INCOMPLETE'}")
        print("\nSample Data (First 3 Books):")
        print("-"*60)
        for i, book in enumerate(self.books_data[:3], 1):
            print(f"\n{i}. {book['title']}")
            print(f"   Price: {book['price']}")
            print(f"   Rating: {book['rating']}")
            print(f"   Stock: {book['stock_availability']}")
        print("\n" + "="*60)


def main():
    """Main execution function"""
    print("="*60)
    print("BOOKS.TOSCRAPE.COM WEB SCRAPER")
    print("="*60)
    print("Initializing scraper...\n")
    
    # Initialize scraper
    scraper = BookScraper(
        base_url="https://books.toscrape.com/",
        min_records=500,
        max_retries=3,
        delay_range=(1, 2)
    )
    
    # Execute scraping
    scraper.scrape()
    
    # Print summary
    scraper.print_summary()
    
    # Export data
    print("\nExporting data...")
    scraper.export_to_csv("books_data.csv")
    scraper.export_to_json("books_data.json")
    
    print("\n✓ Scraping complete! Check the output files:")
    print("  - books_data.csv")
    print("  - books_data.json")
    print("  - scraper.log (for detailed logs)")
    print("="*60)


if __name__ == "__main__":
    main()
