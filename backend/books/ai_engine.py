"""
AI Insight Engine: generates summaries, genre classifications,
sentiment analysis, and book recommendations using LLM APIs.
Supports OpenAI API and LM Studio (local LLM).
Falls back to rule-based methods if no API is available.
"""
import os
import json
import logging
import hashlib
from functools import lru_cache
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory cache for AI responses (avoids redundant API calls)
# ---------------------------------------------------------------------------
_insight_cache = {}


def _cache_key(func_name, text):
    return hashlib.md5(f"{func_name}:{text[:500]}".encode()).hexdigest()


def _get_cached(func_name, text):
    key = _cache_key(func_name, text)
    return _insight_cache.get(key)


def _set_cached(func_name, text, value):
    key = _cache_key(func_name, text)
    _insight_cache[key] = value


# ---------------------------------------------------------------------------
# LLM Client
# ---------------------------------------------------------------------------
def _get_client():
    """Get OpenAI-compatible client (works with OpenAI API and LM Studio)."""
    base_url = os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1')
    api_key = os.getenv('OPENAI_API_KEY', 'lm-studio')
    return OpenAI(base_url=base_url, api_key=api_key)


def _get_model():
    return os.getenv('LLM_MODEL', 'gpt-4o-mini')


def _has_api_key():
    key = os.getenv('OPENAI_API_KEY', '')
    return bool(key) and key != 'your-openai-api-key' and key != 'lm-studio'


def _has_lm_studio():
    return os.getenv('LLM_BASE_URL', '').startswith('http://localhost')


def _llm_available():
    return _has_api_key() or _has_lm_studio()


def _call_llm(system_prompt, user_prompt, max_tokens=300, temperature=0.7):
    """Call the LLM with error handling."""
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=_get_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Summary Generation
# ---------------------------------------------------------------------------
def generate_summary(description):
    """Generate a concise 2-3 sentence summary of the book."""
    if not description or len(description.strip()) < 20:
        return "No description available for summarization."

    # Check cache
    cached = _get_cached('summary', description)
    if cached:
        return cached

    if _llm_available():
        result = _call_llm(
            "You are a literary critic. Generate a concise, engaging 2-3 sentence summary of a book "
            "based on its description. Focus on the main theme, setting, and what makes it compelling.",
            f"Summarize this book:\n\n{description[:2000]}",
            max_tokens=200,
        )
        if result:
            _set_cached('summary', description, result)
            return result

    # Fallback: first 2 sentences
    sentences = description.replace('...', '.').split('.')
    summary = '. '.join(s.strip() for s in sentences[:2] if s.strip())
    if summary and not summary.endswith('.'):
        summary += '.'
    return summary or "No summary available."


# ---------------------------------------------------------------------------
# Genre Classification
# ---------------------------------------------------------------------------
GENRE_LIST = [
    "Literary Fiction", "Romance", "Mystery & Thriller", "Science Fiction",
    "Fantasy", "Horror", "Historical Fiction", "Poetry", "Philosophy",
    "Science & Nature", "Self-Help", "Business", "Biography", "Travel",
    "Humor", "Children's", "Young Adult", "Religion & Spirituality",
    "Art & Music", "Classics", "Non-Fiction",
]


def classify_genre(description, category=''):
    """Predict genre from description text."""
    if not description and not category:
        return "Uncategorized"

    text = f"{category} {description}"
    cached = _get_cached('genre', text)
    if cached:
        return cached

    if _llm_available():
        result = _call_llm(
            f"You are a book genre classifier. Classify the book into exactly ONE genre from this list: "
            f"{', '.join(GENRE_LIST)}. Respond with ONLY the genre name, nothing else.",
            f"Category: {category}\nDescription: {description[:1500]}",
            max_tokens=30,
            temperature=0.3,
        )
        if result and any(g.lower() in result.lower() for g in GENRE_LIST):
            # Extract matched genre
            for g in GENRE_LIST:
                if g.lower() in result.lower():
                    _set_cached('genre', text, g)
                    return g
            _set_cached('genre', text, result)
            return result

    # Fallback: use the site category or simple keyword matching
    if category:
        return category
    return "Uncategorized"


# ---------------------------------------------------------------------------
# Sentiment Analysis
# ---------------------------------------------------------------------------
POSITIVE_WORDS = {'love', 'beautiful', 'wonderful', 'amazing', 'excellent', 'great', 'best',
                  'brilliant', 'masterpiece', 'joy', 'happy', 'enchanting', 'captivating',
                  'inspiring', 'heartwarming', 'delightful', 'charming', 'magnificent'}
NEGATIVE_WORDS = {'dark', 'tragic', 'horror', 'death', 'fear', 'terrible', 'worst',
                  'disturbing', 'brutal', 'violent', 'devastating', 'grim', 'bleak',
                  'haunting', 'sinister', 'chilling', 'painful', 'depressing'}


def analyze_sentiment(description):
    """Analyze the tone of the book description."""
    if not description or len(description.strip()) < 20:
        return "Neutral"

    cached = _get_cached('sentiment', description)
    if cached:
        return cached

    if _llm_available():
        result = _call_llm(
            "You are a sentiment analyzer. Analyze the emotional tone of this book description. "
            "Respond with EXACTLY one of: Positive, Negative, Neutral, Mixed. "
            "Then add a pipe | followed by a confidence score 0-100. Example: 'Positive|85'",
            f"Analyze sentiment:\n\n{description[:1500]}",
            max_tokens=20,
            temperature=0.2,
        )
        if result:
            parts = result.split('|')
            sentiment = parts[0].strip()
            if sentiment in ('Positive', 'Negative', 'Neutral', 'Mixed'):
                _set_cached('sentiment', description, sentiment)
                return sentiment

    # Fallback: keyword-based
    words = set(description.lower().split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos > neg + 1:
        sentiment = "Positive"
    elif neg > pos + 1:
        sentiment = "Negative"
    elif pos > 0 and neg > 0:
        sentiment = "Mixed"
    else:
        sentiment = "Neutral"

    _set_cached('sentiment', description, sentiment)
    return sentiment


# ---------------------------------------------------------------------------
# Recommendation Logic
# ---------------------------------------------------------------------------
def get_recommendations(book, limit=6):
    """Get recommended books based on genre similarity and rating."""
    from .models import Book

    # Strategy 1: same category, high rating
    same_category = list(
        Book.objects.filter(category=book.category)
        .exclude(id=book.id)
        .order_by('-rating')[:limit]
    )

    if len(same_category) >= limit:
        return same_category[:limit]

    # Strategy 2: same genre
    same_genre = list(
        Book.objects.filter(genre=book.genre)
        .exclude(id=book.id)
        .exclude(id__in=[b.id for b in same_category])
        .order_by('-rating')[:limit - len(same_category)]
    )

    results = same_category + same_genre

    # Strategy 3: fill remaining with highest-rated books
    if len(results) < limit:
        filler = list(
            Book.objects.exclude(id=book.id)
            .exclude(id__in=[b.id for b in results])
            .order_by('-rating')[:limit - len(results)]
        )
        results.extend(filler)

    return results[:limit]


# ---------------------------------------------------------------------------
# Batch Processing
# ---------------------------------------------------------------------------
def process_book_insights(book):
    """Generate all AI insights for a single book."""
    logger.info(f"Processing AI insights for: {book.title}")
    book.summary = generate_summary(book.description)
    book.genre = classify_genre(book.description, book.category)
    book.sentiment = analyze_sentiment(book.description)
    book.is_processed = True
    book.save()
    logger.info(f"Insights complete for: {book.title}")
    return book
