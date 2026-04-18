"""
RAG Pipeline: Retrieval-Augmented Generation for book question-answering.
Uses ChromaDB for vector storage and OpenAI/LM Studio for generation.
Supports smart chunking with overlap and embedding caching.
"""
import os
import logging
import hashlib
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ChromaDB Setup
# ---------------------------------------------------------------------------
_chroma_client = None
_collection = None


def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        persist_dir = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')
        os.makedirs(persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
    return _chroma_client


def get_collection():
    global _collection
    if _collection is None:
        client = _get_chroma_client()
        _collection = client.get_or_create_collection(
            name="book_chunks",
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


# ---------------------------------------------------------------------------
# Smart Chunking Strategy
# ---------------------------------------------------------------------------
def chunk_text(text, chunk_size=300, overlap=50):
    """
    Split text into overlapping chunks by word count.
    Uses smart boundary detection (sentence endings) for cleaner chunks.
    """
    if not text or not text.strip():
        return []

    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    i = 0
    while i < len(words):
        end = min(i + chunk_size, len(words))
        chunk_words = words[i:end]
        chunk = ' '.join(chunk_words)

        # Try to end on a sentence boundary for cleaner chunks
        if end < len(words):
            last_period = chunk.rfind('.')
            last_question = chunk.rfind('?')
            last_exclaim = chunk.rfind('!')
            best_break = max(last_period, last_question, last_exclaim)
            if best_break > len(chunk) * 0.6:
                chunk = chunk[:best_break + 1]

        chunks.append(chunk.strip())
        i += chunk_size - overlap

    return chunks


# ---------------------------------------------------------------------------
# Embedding Generation
# ---------------------------------------------------------------------------
_embedding_cache = {}


def _use_openai_embeddings():
    """Check if we can use OpenAI embeddings."""
    key = os.getenv('OPENAI_API_KEY', '')
    base_url = os.getenv('LLM_BASE_URL', '')
    return (bool(key) and key != 'your-openai-api-key' and key != 'lm-studio') or \
           base_url.startswith('http://localhost')


def generate_embedding(text):
    """Generate embedding vector for text. Uses OpenAI API or returns None for ChromaDB default."""
    cache_key = hashlib.md5(text[:500].encode()).hexdigest()
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]

    if _use_openai_embeddings():
        try:
            client = OpenAI(
                base_url=os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1'),
                api_key=os.getenv('OPENAI_API_KEY', 'lm-studio'),
            )
            response = client.embeddings.create(
                model=os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small'),
                input=text[:8000],
            )
            embedding = response.data[0].embedding
            _embedding_cache[cache_key] = embedding
            return embedding
        except Exception as e:
            logger.warning(f"OpenAI embedding failed, using ChromaDB default: {e}")
            return None
    return None


# ---------------------------------------------------------------------------
# Book Indexing
# ---------------------------------------------------------------------------
def index_book(book):
    """Index a book's text into ChromaDB for RAG retrieval."""
    from .models import BookChunk

    text = f"Title: {book.title}.\n"
    if book.author and book.author != 'Unknown':
        text += f"Author: {book.author}.\n"
    text += f"Category: {book.category}.\n"
    if book.description:
        text += f"Description: {book.description}\n"
    if book.summary:
        text += f"Summary: {book.summary}\n"

    chunks = chunk_text(text)
    if not chunks:
        return

    collection = get_collection()

    ids = []
    documents = []
    metadatas = []
    embeddings_list = []
    use_custom_embeddings = _use_openai_embeddings()

    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(f"{book.id}_{i}_{chunk[:100]}".encode()).hexdigest()
        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append({
            "book_id": book.id,
            "title": book.title,
            "chunk_index": i,
            "category": book.category or '',
        })

        if use_custom_embeddings:
            emb = generate_embedding(chunk)
            if emb:
                embeddings_list.append(emb)

        # Save chunk to database
        BookChunk.objects.update_or_create(
            book=book, chunk_index=i,
            defaults={'chunk_text': chunk, 'embedding_id': chunk_id}
        )

    # Add to ChromaDB (with or without custom embeddings)
    try:
        if embeddings_list and len(embeddings_list) == len(ids):
            collection.upsert(
                ids=ids,
                embeddings=embeddings_list,
                documents=documents,
                metadatas=metadatas,
            )
        else:
            # Let ChromaDB use its default embedding function
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
        logger.info(f"Indexed {len(chunks)} chunks for: {book.title}")
    except Exception as e:
        logger.error(f"ChromaDB indexing error for {book.title}: {e}")


# ---------------------------------------------------------------------------
# RAG Query Pipeline
# ---------------------------------------------------------------------------
def query_books(question, top_k=5):
    """
    Full RAG pipeline:
    1. Generate embedding for the question
    2. Similarity search across book chunks
    3. Construct context from retrieved chunks
    4. Generate answer with LLM using source citations
    """
    collection = get_collection()

    # Check if collection has any data
    if collection.count() == 0:
        return {
            'answer': 'No books have been indexed yet. Please scrape or upload some books first.',
            'sources': [],
            'context_chunks': [],
        }

    # Step 1 & 2: Query ChromaDB
    try:
        question_embedding = generate_embedding(question)
        if question_embedding:
            results = collection.query(
                query_embeddings=[question_embedding],
                n_results=min(top_k, collection.count()),
            )
        else:
            results = collection.query(
                query_texts=[question],
                n_results=min(top_k, collection.count()),
            )
    except Exception as e:
        logger.error(f"ChromaDB query error: {e}")
        return {
            'answer': f'Error searching the book database: {str(e)}',
            'sources': [],
            'context_chunks': [],
        }

    # Step 3: Construct context
    context_parts = []
    sources = []
    seen_books = set()

    if results and results.get('documents') and results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            distance = results['distances'][0][i] if results.get('distances') else 0
            context_parts.append(f"[Source: {meta['title']}]\n{doc}")
            if meta['title'] not in seen_books:
                sources.append({
                    "title": meta['title'],
                    "book_id": meta.get('book_id', 0),
                    "relevance": round(1 - distance, 3) if distance else 0,
                })
                seen_books.add(meta['title'])

    context = "\n\n---\n\n".join(context_parts)

    if not context:
        return {
            'answer': 'No relevant book information found for your question.',
            'sources': [],
            'context_chunks': [],
        }

    # Step 4: Generate answer with LLM
    key = os.getenv('OPENAI_API_KEY', '')
    base_url = os.getenv('LLM_BASE_URL', '')
    has_llm = (bool(key) and key != 'your-openai-api-key') or base_url.startswith('http://localhost')

    if has_llm:
        try:
            client = OpenAI(
                base_url=base_url or 'https://api.openai.com/v1',
                api_key=key or 'lm-studio',
            )
            response = client.chat.completions.create(
                model=os.getenv('LLM_MODEL', 'gpt-4o-mini'),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a knowledgeable book expert and literary assistant. "
                            "Answer questions using ONLY the provided context from the book database. "
                            "Always cite which book(s) your answer is based on. "
                            "If the context doesn't contain enough information, say so honestly."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Context from book database:\n{context}\n\n"
                                   f"Question: {question}\n\n"
                                   f"Provide a detailed answer with source citations."
                    },
                ],
                max_tokens=600,
                temperature=0.5,
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            answer = f"Based on the retrieved context:\n\n{context_parts[0][:500]}..."
    else:
        # Fallback: return raw context
        answer = (
            "AI response generation requires an API key. "
            "Here are the most relevant passages found:\n\n"
            + "\n\n".join(context_parts[:3])
        )

    return {
        'answer': answer,
        'sources': sources,
        'context_chunks': [{'text': cp[:300], 'source': s.get('title', '')}
                           for cp, s in zip(context_parts, sources)],
    }
