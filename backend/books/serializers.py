from rest_framework import serializers
from .models import Book, BookChunk


class BookListSerializer(serializers.ModelSerializer):
    """Serializer for book listing (lighter payload)."""
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'rating', 'num_reviews', 'price',
            'book_url', 'cover_image_url', 'category', 'genre',
            'summary', 'sentiment', 'is_processed', 'created_at',
        ]


class BookChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookChunk
        fields = ['id', 'chunk_text', 'chunk_index']


class BookDetailSerializer(serializers.ModelSerializer):
    """Full book detail including chunks."""
    chunks = BookChunkSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = '__all__'


class BookUploadSerializer(serializers.ModelSerializer):
    """Serializer for book upload/creation."""
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'rating', 'num_reviews', 'price',
            'description', 'book_url', 'cover_image_url', 'category',
        ]


class QuestionSerializer(serializers.Serializer):
    """Serializer for RAG question input."""
    question = serializers.CharField(max_length=1000)
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=20)
