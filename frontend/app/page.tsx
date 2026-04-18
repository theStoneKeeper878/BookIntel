'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { fetchBooks, scrapeBooks, getScrapeStatus, Book, ScrapeStatus } from '@/lib/api';

/* ===== Star Rating ===== */
function Stars({ rating }: { rating: number }) {
  return (
    <span className="stars">
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={`star ${i <= rating ? 'filled' : ''}`}>★</span>
      ))}
    </span>
  );
}

/* ===== Sentiment Badge ===== */
function SentimentBadge({ sentiment }: { sentiment: string }) {
  const map: Record<string, string> = {
    Positive: 'badge-emerald',
    Negative: 'badge-rose',
    Mixed: 'badge-amber',
    Neutral: 'badge-blue',
  };
  return <span className={`badge ${map[sentiment] || 'badge-blue'}`}>{sentiment || 'N/A'}</span>;
}

/* ===== Book Card ===== */
function BookCard({ book }: { book: Book }) {
  return (
    <Link href={`/books/${book.id}`} style={{ textDecoration: 'none' }}>
      <div className="glass-card" style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Cover image */}
        <div
          style={{
            height: '180px',
            background: book.cover_image_url
              ? `url(${book.cover_image_url}) center/cover`
              : 'linear-gradient(135deg, rgba(124,58,237,0.2), rgba(59,130,246,0.2))',
            borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
          }}
        >
          {!book.cover_image_url && (
            <span style={{ fontSize: '3rem', opacity: 0.4 }}>📖</span>
          )}
          {book.genre && (
            <span
              className="badge badge-violet"
              style={{ position: 'absolute', top: '12px', right: '12px' }}
            >
              {book.genre}
            </span>
          )}
        </div>

        {/* Content */}
        <div style={{ padding: '16px', flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h3
            style={{
              fontSize: '0.9375rem',
              fontWeight: 600,
              lineHeight: 1.3,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              color: 'var(--text-primary)',
            }}
          >
            {book.title}
          </h3>

          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
            {book.author}
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: 'auto' }}>
            <Stars rating={book.rating} />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              ({book.num_reviews})
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
            {book.category && <span className="badge badge-blue">{book.category}</span>}
            <SentimentBadge sentiment={book.sentiment} />
          </div>

          {book.price != null && (
            <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--accent-emerald)' }}>
              £{Number(book.price).toFixed(2)}
            </p>
          )}
        </div>
      </div>
    </Link>
  );
}

/* ===== Skeleton Card ===== */
function SkeletonCard() {
  return (
    <div className="glass-card" style={{ overflow: 'hidden' }}>
      <div className="skeleton" style={{ height: '180px', borderRadius: 0 }} />
      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div className="skeleton" style={{ height: '18px', width: '85%' }} />
        <div className="skeleton" style={{ height: '14px', width: '50%' }} />
        <div className="skeleton" style={{ height: '14px', width: '60%' }} />
        <div className="skeleton" style={{ height: '22px', width: '30%' }} />
      </div>
    </div>
  );
}

/* ===== Scrape Progress Bar ===== */
function ScrapeProgress({ status }: { status: ScrapeStatus }) {
  const pct = status.total > 0 ? (status.progress / status.total) * 100 : 0;
  return (
    <div
      className="glass-card pulse-glow"
      style={{ padding: '20px', marginBottom: '24px' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
        <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>
          🔄 Scraping in progress...
        </span>
        <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
          {status.progress} / {status.total} books
        </span>
      </div>
      <div
        style={{
          height: '6px',
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '3px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${pct}%`,
            background: 'var(--gradient-primary)',
            borderRadius: '3px',
            transition: 'width 0.5s ease',
          }}
        />
      </div>
      {status.current_book && (
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px' }}>
          Current: {status.current_book}
        </p>
      )}
    </div>
  );
}

/* ===== Main Dashboard Page ===== */
export default function DashboardPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [scrapeStatus, setScrapeStatus] = useState<ScrapeStatus | null>(null);
  const [error, setError] = useState('');
  const [totalCount, setTotalCount] = useState(0);

  const loadBooks = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchBooks({ search, ordering: '-rating' });
      setBooks(data.results);
      setTotalCount(data.count);
    } catch {
      setError('Failed to connect to backend. Is the server running?');
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    loadBooks();
  }, [loadBooks]);

  // Poll scrape status
  useEffect(() => {
    if (!scrapeStatus?.is_running) return;
    const interval = setInterval(async () => {
      const s = await getScrapeStatus();
      setScrapeStatus(s);
      if (!s.is_running) {
        clearInterval(interval);
        loadBooks();
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [scrapeStatus?.is_running, loadBooks]);

  const handleScrape = async () => {
    try {
      await scrapeBooks(30);
      setScrapeStatus({ is_running: true, progress: 0, total: 30, current_book: '', error: null });
    } catch {
      setError('Failed to start scraper');
    }
  };

  return (
    <div className="animate-fade-in">
      {/* Hero Section */}
      <section style={{ textAlign: 'center', padding: '40px 0 32px' }}>
        <h1
          className="gradient-text"
          style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: '12px' }}
        >
          Document Intelligence Platform
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.0625rem', maxWidth: '600px', margin: '0 auto' }}>
          AI-powered book analysis with automated scraping, smart insights, and RAG-based question answering.
        </p>
      </section>

      {/* Controls */}
      <div
        style={{
          display: 'flex',
          gap: '12px',
          marginBottom: '24px',
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        <div style={{ flex: 1, minWidth: '240px' }}>
          <input
            id="search-input"
            className="input-field"
            type="text"
            placeholder="Search books by title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button
          id="scrape-btn"
          className="btn-primary"
          onClick={handleScrape}
          disabled={scrapeStatus?.is_running}
          style={{ whiteSpace: 'nowrap' }}
        >
          {scrapeStatus?.is_running ? '⏳ Scraping...' : 'Search Books'}
        </button>
        <div
          style={{
            padding: '10px 16px',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.8125rem',
            color: 'var(--text-secondary)',
          }}
        >
          {totalCount} books
        </div>
      </div>

      {/* Scrape Progress */}
      {scrapeStatus?.is_running && <ScrapeProgress status={scrapeStatus} />}

      {/* Error */}
      {error && (
        <div
          style={{
            padding: '16px',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid rgba(244, 63, 94, 0.2)',
            color: '#fda4af',
            marginBottom: '24px',
            fontSize: '0.875rem',
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* Book Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          gap: '20px',
        }}
      >
        {loading
          ? Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)
          : books.map((book, i) => (
            <div key={book.id} className="animate-slide-up" style={{ animationDelay: `${i * 0.05}s` }}>
              <BookCard book={book} />
            </div>
          ))
        }
      </div>

      {/* Empty State */}
      {!loading && books.length === 0 && !error && (
        <div
          style={{
            textAlign: 'center',
            padding: '60px 20px',
          }}
        >
          {/* <p style={{ fontSize: '3rem', marginBottom: '16px' }}>📚</p> */}
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '8px' }}>No books yet</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
            Click &quot;Below &quot; to automatically collect book data from the web.
          </p>
          <button className="btn-primary" onClick={handleScrape}>
            Show ALL BOOKS
          </button>
        </div>
      )}
    </div>
  );
}
