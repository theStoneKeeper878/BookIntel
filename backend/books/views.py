"""
REST API Views for the Document Intelligence Platform.
Provides endpoints for book CRUD, scraping, AI insights, and RAG Q&A.
"""
import threading
import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Book, BookChunk
from .serializers import (
    BookListSerializer, BookDetailSerializer,
    BookUploadSerializer, QuestionSerializer,
)
from .scraper import BookScraper
from .ai_engine import process_book_insights, get_recommendations
from .rag import index_book, query_books

logger = logging.getLogger(__name__)

# Simple in-memory scrape status tracker
_scrape_status = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_book': '',
    'error': None,
}


# ---------------------------------------------------------------------------
# GET Endpoints
# ---------------------------------------------------------------------------
class BookListView(generics.ListAPIView):
    """GET /api/books/ — List all uploaded books."""
    serializer_class = BookListSerializer

    def get_queryset(self):
        qs = Book.objects.all()
        search = self.request.query_params.get('search', '')
        if search:
            qs = qs.filter(title__icontains=search)
        category = self.request.query_params.get('category', '')
        if category:
            qs = qs.filter(category__iexact=category)
        genre = self.request.query_params.get('genre', '')
        if genre:
            qs = qs.filter(genre__iexact=genre)
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering in ('title', '-title', 'rating', '-rating', 'created_at', '-created_at'):
            qs = qs.order_by(ordering)
        return qs


class BookDetailView(generics.RetrieveAPIView):
    """GET /api/books/{id}/ — Retrieve full book details."""
    queryset = Book.objects.all()
    serializer_class = BookDetailSerializer


class BookRecommendationsView(APIView):
    """GET /api/books/{id}/recommendations/ — Get related book recommendations."""

    def get(self, request, pk):
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=404)

        recommendations = get_recommendations(book, limit=6)
        serializer = BookListSerializer(recommendations, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------
class BookUploadView(APIView):
    """POST /api/books/upload/ — Upload and process a new book."""

    def post(self, request):
        serializer = BookUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        book = serializer.save()

        # Process AI insights
        try:
            process_book_insights(book)
        except Exception as e:
            logger.error(f"AI processing error: {e}")

        # Index for RAG
        try:
            index_book(book)
        except Exception as e:
            logger.error(f"RAG indexing error: {e}")

        return Response(
            BookDetailSerializer(book).data,
            status=status.HTTP_201_CREATED,
        )


class BookScrapeView(APIView):
    """POST /api/books/scrape/ — Trigger Selenium scraper."""

    def post(self, request):
        global _scrape_status

        if _scrape_status['is_running']:
            return Response({
                'status': 'already_running',
                'progress': _scrape_status['progress'],
                'total': _scrape_status['total'],
            }, status=409)

        max_books = int(request.data.get('max_books', 30))
        max_books = min(max_books, 200)

        _scrape_status = {
            'is_running': True,
            'progress': 0,
            'total': max_books,
            'current_book': '',
            'error': None,
        }

        thread = threading.Thread(
            target=self._run_scraper,
            args=(max_books,),
            daemon=True,
        )
        thread.start()

        return Response({
            'status': 'started',
            'max_books': max_books,
            'message': f'Scraping up to {max_books} books in the background.',
        })

    @staticmethod
    def _run_scraper(max_books):
        global _scrape_status
        try:
            def progress_cb(current, total, title):
                _scrape_status['progress'] = current
                _scrape_status['total'] = total
                _scrape_status['current_book'] = title

            scraper = BookScraper(max_books=max_books)
            books_data = scraper.scrape(progress_callback=progress_cb)

            for data in books_data:
                upc = data.pop('upc', '')
                book, created = Book.objects.update_or_create(
                    upc=upc,
                    defaults={**data, 'upc': upc},
                )
                if created or not book.is_processed:
                    try:
                        process_book_insights(book)
                    except Exception as e:
                        logger.error(f"AI error for {book.title}: {e}")
                    try:
                        index_book(book)
                    except Exception as e:
                        logger.error(f"Index error for {book.title}: {e}")

            _scrape_status['is_running'] = False
            _scrape_status['progress'] = _scrape_status['total']
            logger.info("Scraping pipeline complete.")

        except Exception as e:
            logger.error(f"Scraper error: {e}")
            _scrape_status['is_running'] = False
            _scrape_status['error'] = str(e)


class ScrapeStatusView(APIView):
    """GET /api/books/scrape-status/ — Check scraper progress."""

    def get(self, request):
        return Response(_scrape_status)


class BookAskView(APIView):
    """POST /api/books/ask/ — RAG question-answering over books."""

    def post(self, request):
        serializer = QuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        question = serializer.validated_data['question']
        top_k = serializer.validated_data.get('top_k', 5)

        result = query_books(question, top_k=top_k)
        return Response(result)
