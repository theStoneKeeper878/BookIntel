from django.urls import path
from . import views

urlpatterns = [
    # GET endpoints
    path('books/', views.BookListView.as_view(), name='book-list'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('books/<int:pk>/recommendations/', views.BookRecommendationsView.as_view(), name='book-recommendations'),

    # POST endpoints
    path('books/upload/', views.BookUploadView.as_view(), name='book-upload'),
    path('books/scrape/', views.BookScrapeView.as_view(), name='book-scrape'),
    path('books/ask/', views.BookAskView.as_view(), name='book-ask'),

    # Status
    path('books/scrape-status/', views.ScrapeStatusView.as_view(), name='scrape-status'),
]
