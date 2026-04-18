"""
Management command to run the book scraper from the CLI.
Usage: python manage.py scrape_books --max 50
"""
from django.core.management.base import BaseCommand
from books.scraper import BookScraper
from books.ai_engine import process_book_insights
from books.rag import index_book


class Command(BaseCommand):
    help = 'Scrape books from books.toscrape.com and process with AI'

    def add_arguments(self, parser):
        parser.add_argument('--max', type=int, default=30, help='Max books to scrape')
        parser.add_argument('--skip-ai', action='store_true', help='Skip AI processing')
        parser.add_argument('--skip-index', action='store_true', help='Skip RAG indexing')

    def handle(self, *args, **options):
        from books.models import Book

        max_books = options['max']
        self.stdout.write(f"Starting scraper for up to {max_books} books...")

        scraper = BookScraper(max_books=max_books)
        books_data = scraper.scrape()

        self.stdout.write(f"Scraped {len(books_data)} books. Saving to database...")

        for data in books_data:
            upc = data.pop('upc', '')
            book, created = Book.objects.update_or_create(
                upc=upc, defaults={**data, 'upc': upc},
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(f"  {action}: {book.title}")

            if not options['skip_ai'] and (created or not book.is_processed):
                try:
                    process_book_insights(book)
                    self.stdout.write(f"    AI insights generated")
                except Exception as e:
                    self.stderr.write(f"    AI error: {e}")

            if not options['skip_index']:
                try:
                    index_book(book)
                    self.stdout.write(f"    RAG indexed")
                except Exception as e:
                    self.stderr.write(f"    Index error: {e}")

        self.stdout.write(self.style.SUCCESS(f"Done! {len(books_data)} books processed."))
