"""
Selenium-based web scraper for books.toscrape.com.
Collects book metadata including title, price, rating, description, and category.
"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

RATING_MAP = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5
}


class BookScraper:
    """Scrapes book data from books.toscrape.com using Selenium."""
    BASE_URL = "https://books.toscrape.com"

    def __init__(self, max_books=50):
        self.max_books = max_books
        self.driver = None

    def _init_driver(self):
        """Initialize headless Chrome WebDriver."""
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception:
            self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)

    def _get_book_links(self, page_num):
        """Get all book detail links from a catalogue page."""
        url = f"{self.BASE_URL}/catalogue/page-{page_num}.html"
        self.driver.get(url)
        time.sleep(1)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        articles = soup.select('article.product_pod')

        links = []
        for article in articles:
            link_el = article.select_one('h3 a')
            if link_el:
                href = link_el.get('href', '')
                if href.startswith('../'):
                    href = href.replace('../', '')
                if not href.startswith('http'):
                    href = f"{self.BASE_URL}/catalogue/{href}"
                links.append(href)
        return links

    def _get_book_detail(self, url):
        """Scrape full details from a book's detail page."""
        self.driver.get(url)
        time.sleep(0.5)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Title
        title_el = soup.select_one('div.product_main h1')
        title = title_el.text.strip() if title_el else 'Unknown Title'

        # Price
        price_el = soup.select_one('p.price_color')
        price_text = price_el.text.strip() if price_el else '0'
        price = float(''.join(c for c in price_text if c.isdigit() or c == '.') or '0')

        # Rating
        rating = 0
        rating_el = soup.select_one('p.star-rating')
        if rating_el:
            for cls in rating_el.get('class', []):
                if cls.lower() in RATING_MAP:
                    rating = RATING_MAP[cls.lower()]
                    break

        # Description
        desc_el = soup.select_one('#product_description ~ p')
        description = desc_el.text.strip() if desc_el else ''

        # Category from breadcrumb
        breadcrumbs = soup.select('ul.breadcrumb li')
        category = breadcrumbs[2].text.strip() if len(breadcrumbs) > 2 else ''

        # Cover Image
        img_el = soup.select_one('#product_gallery img')
        cover_url = ''
        if img_el and img_el.get('src'):
            src = img_el['src']
            if src.startswith('../../'):
                cover_url = f"{self.BASE_URL}/{src.replace('../../', '')}"
            elif not src.startswith('http'):
                cover_url = f"{self.BASE_URL}/{src}"
            else:
                cover_url = src

        # Product info table
        table_cells = soup.select('table.table-striped td')
        upc = table_cells[0].text.strip() if len(table_cells) > 0 else ''
        availability = table_cells[5].text.strip() if len(table_cells) > 5 else ''
        num_reviews = 0
        if len(table_cells) > 6:
            try:
                num_reviews = int(table_cells[6].text.strip())
            except ValueError:
                pass

        return {
            'title': title,
            'author': 'Unknown',
            'price': price,
            'rating': rating,
            'description': description,
            'category': category,
            'cover_image_url': cover_url,
            'book_url': url,
            'upc': upc,
            'availability': availability,
            'num_reviews': num_reviews,
        }

    def scrape(self, progress_callback=None):
        """
        Scrape books from books.toscrape.com.
        Returns a list of book data dictionaries.
        """
        self._init_driver()
        books = []

        try:
            page = 1
            while len(books) < self.max_books:
                logger.info(f"Scraping page {page}...")
                links = self._get_book_links(page)

                if not links:
                    logger.info("No more pages to scrape.")
                    break

                for link in links:
                    if len(books) >= self.max_books:
                        break
                    try:
                        book_data = self._get_book_detail(link)
                        books.append(book_data)
                        logger.info(f"[{len(books)}/{self.max_books}] Scraped: {book_data['title']}")
                        if progress_callback:
                            progress_callback(len(books), self.max_books, book_data['title'])
                    except Exception as e:
                        logger.error(f"Error scraping {link}: {e}")

                page += 1

        finally:
            if self.driver:
                self.driver.quit()

        logger.info(f"Scraping complete. Total books: {len(books)}")
        return books
