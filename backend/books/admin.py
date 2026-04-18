from django.contrib import admin
from .models import Book, BookChunk


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'rating', 'category', 'genre', 'is_processed', 'created_at']
    list_filter = ['is_processed', 'category', 'genre', 'sentiment']
    search_fields = ['title', 'author', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BookChunk)
class BookChunkAdmin(admin.ModelAdmin):
    list_display = ['book', 'chunk_index', 'embedding_id']
    list_filter = ['book']
