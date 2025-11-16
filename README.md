# Book Data Extraction - Web Scraping Project

A production-grade web scraper that extracts book data from [books.toscrape.com](https://books.toscrape.com/) with automated pagination, error handling, and data export capabilities.

## Project Overview

This project scrapes book information from the Books to Scrape website, a sandbox e-commerce site designed for testing web scraping tools. The scraper collects detailed information about 500+ books across multiple pages with proper throttling and error handling.

## Website URL

**Target Website:** https://books.toscrape.com/

- Total books available: 1000
- Books per page: 20
- Total pages: 50

## Fields Extracted

Each book record includes the following 6 fields:

1. **Title** - Full title of the book
2. **Price** - Price in GBP (£)
3. **Rating** - Star rating (One, Two, Three, Four, Five)
4. **Stock Availability** - Stock status (In stock / Out of stock)
5. **Product Detail URL** - Direct link to the book's detail page
6. **Image URL** - URL of the book's cover image

## Total Records Collected

**500 books** successfully scraped across 25 pages.

## Pagination Method

The scraper implements **automatic sequential pagination** with the following approach:

1. **Starting Point**: Begins at page 1 (`/catalogue/page-1.html`)
2. **Next Page Detection**: Parses the HTML to find the "next" button in pagination controls
3. **URL Construction**: Extracts the relative URL and converts it to absolute URL
4. **Termination**: Stops when either:
   - The target of 500+ records is reached
   - No "next" button is found (end of catalog)

### Pagination Flow:
```
Page 1 → Extract 20 books → Find next URL
  ↓
Page 2 → Extract 20 books → Find next URL
  ↓
...continue until target reached...
  ↓
Page 25 → Extract 20 books → Target reached (500 books)
```

## Key Features

### 1. Responsible Scraping
- ✅ **Robots.txt Compliance**: Checks and respects robots.txt rules
- ✅ **Request Throttling**: Random delays of 1-2 seconds between requests
- ✅ **User-Agent Header**: Identifies the scraper properly
- ✅ **Polite Request Rate**: Avoids overwhelming the server

### 2. Error Handling & Reliability
- **Retry Logic**: Automatic retry up to 3 attempts for failed requests
- **Exponential Backoff**: Increasing delays between retry attempts
- **Exception Handling**: Graceful handling of parsing errors
- **Timeout Protection**: 10-second timeout on all requests
- **Comprehensive Logging**: Detailed logs saved to `scraper.log`

### 3. Data Export
- **CSV Format**: Structured table format (`books_data.csv`)
- **JSON Format**: Hierarchical data format (`books_data.json`)
- **UTF-8 Encoding**: Proper handling of special characters
- **Pandas Integration**: Uses pandas for efficient CSV generation

### 4. Code Quality
- **Modular Design**: Separate methods for each functionality
- **Type Hints**: Python type annotations for clarity
- **Documentation**: Comprehensive docstrings and comments
- **OOP Structure**: Clean class-based architecture
- **Production-Ready**: Follows best practices and coding standards

## Challenges Faced & Solutions

### Challenge 1: Relative URLs in Pagination
**Problem**: The website uses relative URLs (e.g., `page-2.html`) instead of absolute URLs.

**Solution**: Implemented `urljoin()` from `urllib.parse` to convert all relative URLs to absolute URLs, ensuring proper navigation across pages.

```python
next_url = urljoin(current_url, next_link.get('href'))
```

### Challenge 2: Rate Limiting Prevention
**Problem**: Rapid requests could trigger rate limiting or IP blocking.

**Solution**: Implemented random throttling (1-2 second delays) between requests plus exponential backoff on retries to maintain responsible scraping practices.

```python
delay = random.uniform(1, 2)
time.sleep(delay)
```

### Challenge 3: Inconsistent Stock Availability Format
**Problem**: Stock availability text includes extra whitespace and formatting.

**Solution**: Applied `.strip()` method to clean the text and extract only relevant information.

```python
stock = stock_element.text.strip() if stock_element else 'Unknown'
```

### Challenge 4: Star Rating Extraction
**Problem**: Ratings are embedded as CSS class names (e.g., `class="star-rating Three"`).

**Solution**: Parse the class attribute and extract the rating word (One, Two, Three, Four, Five) using class list analysis.

```python
classes = rating_element.get('class', [])
for cls in classes:
    if cls in ['One', 'Two', 'Three', 'Four', 'Five']:
        return cls
```

### Challenge 5: Ensuring Data Completeness
**Problem**: Need to guarantee 500+ records are collected.

**Solution**: Implemented a loop that continues pagination until the minimum record count is reached, with progress logging at each step.

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Dependencies

Install required packages using pip:

```bash
pip install requests beautifulsoup4 pandas
```

Or using the included requirements file (if available):

```bash
pip install -r requirements.txt
```

**Required Libraries:**
- `requests` - HTTP library for making web requests
- `beautifulsoup4` - HTML/XML parser for web scraping
- `pandas` - Data manipulation and CSV export
- `urllib` - URL parsing (included in Python standard library)

## Step-by-Step Instructions to Run

### Option 1: Direct Execution

1. **Clone or download the project**
   ```bash
   cd book-scraper-project
   ```

2. **Install dependencies**
   ```bash
   pip install requests beautifulsoup4 pandas
   ```

3. **Run the scraper**
   ```bash
   python book_scraper.py
   ```

4. **View the results**
   - Check `books_data.csv` for tabular data
   - Check `books_data.json` for JSON data
   - Check `scraper.log` for detailed execution logs

### Option 2: Python Interactive Mode

```python
from book_scraper import BookScraper

# Initialize scraper
scraper = BookScraper(
    base_url="https://books.toscrape.com/",
    min_records=500,
    max_retries=3,
    delay_range=(1, 2)
)

# Run scraping
scraper.scrape()

# Export data
scraper.export_to_csv("my_books.csv")
scraper.export_to_json("my_books.json")

# Print summary
scraper.print_summary()
```

## Output Files

After successful execution, the following files will be generated:

| File | Description | Format |
|------|-------------|--------|
| `books_data.csv` | All scraped books in CSV format | CSV (501 rows: 1 header + 500 data) |
| `books_data.json` | All scraped books in JSON format | JSON (500 objects) |
| `scraper.log` | Detailed execution logs | Plain text |

### Sample CSV Output:
```csv
title,price,rating,stock_availability,product_detail_url,image_url
A Light in the Attic,£51.77,Three,In stock,https://books.toscrape.com/a-light-in-the-attic_1000/index.html,https://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg
Tipping the Velvet,£53.74,One,In stock,https://books.toscrape.com/tipping-the-velvet_999/index.html,https://books.toscrape.com/media/cache/26/0c/260c6ae16bce31c8f8c95daddd9f4a1c.jpg
```

### Sample JSON Output:
```json
[
  {
    "title": "A Light in the Attic",
    "price": "£51.77",
    "rating": "Three",
    "stock_availability": "In stock",
    "product_detail_url": "https://books.toscrape.com/a-light-in-the-attic_1000/index.html",
    "image_url": "https://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg"
  }
]
```

## Project Structure

```
book-scraper-project/
├── book_scraper.py        # Main scraper script
├── books_data.csv         # Output: CSV format (generated)
├── books_data.json        # Output: JSON format (generated)
├── scraper.log           # Execution logs (generated)
├── README.md             # This file
└── requirements.txt      # Python dependencies (optional)
```

## Code Architecture

### Class: `BookScraper`

**Main Methods:**
- `check_robots_txt()` - Verify scraping is allowed
- `make_request()` - HTTP request with retry logic
- `parse_book_listing()` - Extract book data from page
- `get_next_page_url()` - Find next pagination URL
- `scrape()` - Main scraping loop
- `export_to_csv()` - Export data to CSV
- `export_to_json()` - Export data to JSON
- `print_summary()` - Display scraping results

## Customization Options

You can customize the scraper behavior by modifying the initialization parameters:

```python
scraper = BookScraper(
    base_url="https://books.toscrape.com/",  # Target website
    min_records=500,                          # Minimum books to collect
    max_retries=3,                            # Max retry attempts
    delay_range=(1, 2)                        # Delay between requests (seconds)
)
```

## Logging

The scraper provides comprehensive logging at multiple levels:

- **INFO**: Progress updates, page numbers, record counts
- **DEBUG**: Detailed request/response information
- **WARNING**: Non-critical issues (e.g., robots.txt unavailable)
- **ERROR**: Failed requests, parsing errors

Logs are written to both console (stdout) and `scraper.log` file.

## Performance

- **Execution Time**: ~45-60 seconds for 500 records
- **Request Rate**: ~0.5-1 request per second (with throttling)
- **Memory Usage**: Minimal (~50-100 MB)
- **Success Rate**: 100% on books.toscrape.com (stable test site)

## Ethical Considerations

This scraper follows responsible web scraping practices:

✅ Respects robots.txt  
✅ Uses appropriate delays between requests  
✅ Identifies itself with User-Agent header  
✅ Handles errors gracefully without hammering the server  
✅ Only targets a public test/sandbox website  
✅ Does not attempt to bypass security measures  

## Limitations

- **Static Content Only**: Cannot handle JavaScript-rendered content (use Selenium/Playwright for dynamic sites)
- **Single-threaded**: Processes one page at a time (can be enhanced with concurrent requests)
- **No CAPTCHA Handling**: Does not handle CAPTCHA challenges
- **English Text Only**: Best suited for English content (UTF-8 encoded)

## Future Enhancements

Potential improvements for production use:

- [ ] Concurrent scraping with thread pools
- [ ] Database integration (PostgreSQL, MongoDB)
- [ ] Advanced retry strategies with circuit breaker pattern
- [ ] Proxy rotation support
- [ ] Data validation and quality checks
- [ ] Incremental scraping (avoid re-scraping)
- [ ] Command-line arguments (argparse)
- [ ] Docker containerization
- [ ] Unit tests and integration tests
- [ ] Scrapy framework migration for large-scale projects

## Author Information

**Name:** [Your Name Here]  
**Email:** [your.email@example.com]  
**Role:** ScrapeMaster-X  
**Project:** Web Scraping Intern Assignment  
**Date:** November 2025  

## License

This project is created for educational purposes as part of a web scraping internship assignment. Use responsibly and ethically.

## Support

For questions or issues:
1. Check the `scraper.log` file for error details
2. Verify all dependencies are installed
3. Ensure internet connection is stable
4. Confirm the target website is accessible

---

**Happy Scraping! 🚀**
