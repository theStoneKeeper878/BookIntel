from django.db import models


class Book(models.Model):
    """Stores book metadata and AI-generated insights."""
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=300, blank=True, default='Unknown')
    rating = models.FloatField(default=0)
    num_reviews = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, default='')
    book_url = models.URLField(max_length=1000, blank=True, default='')
    cover_image_url = models.URLField(max_length=1000, blank=True, default='')
    category = models.CharField(max_length=200, blank=True, default='')

    # AI-generated fields
    genre = models.CharField(max_length=200, blank=True, default='')
    summary = models.TextField(blank=True, default='')
    sentiment = models.CharField(max_length=50, blank=True, default='')
    sentiment_score = models.FloatField(default=0)

    # Metadata
    upc = models.CharField(max_length=100, blank=True, default='')
    availability = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class BookChunk(models.Model):
    """Stores text chunks for RAG pipeline vector search."""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chunks')
    chunk_text = models.TextField()
    chunk_index = models.IntegerField()
    embedding_id = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        ordering = ['chunk_index']
        unique_together = ['book', 'chunk_index']

    def __str__(self):
        return f"{self.book.title} - Chunk {self.chunk_index}"
