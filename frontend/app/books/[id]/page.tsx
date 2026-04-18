'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { fetchBook, fetchRecommendations, Book } from '@/lib/api';

/* ===== Stars ===== */
function Stars({ rating }: { rating: number }) {
  return (
    <span className="stars" style={{ fontSize: '1.125rem' }}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={`star ${i <= rating ? 'filled' : ''}`}>★</span>
      ))}
    </span>
  );
}

/* ===== Insight Card ===== */
function InsightCard({ icon, title, content, color }: {
  icon: string; title: string; content: string; color: string;
}) {
  return (
    <div
      className="glass-card"
      style={{
        padding: '20px',
        borderLeft: `3px solid ${color}`,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
        <span style={{ fontSize: '1.25rem' }}>{icon}</span>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
          {title}
        </h3>
      </div>
      <p style={{ fontSize: '0.9375rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
        {content || 'Not available'}
      </p>
    </div>
  );
}

/* ===== Recommendation Card ===== */
function RecCard({ book }: { book: Book }) {
  return (
    <Link href={`/books/${book.id}`} style={{ textDecoration: 'none' }}>
      <div className="glass-card" style={{ padding: '14px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <div
          style={{
            width: '48px',
            height: '64px',
            borderRadius: '6px',
            background: book.cover_image_url
              ? `url(${book.cover_image_url}) center/cover`
              : 'linear-gradient(135deg, rgba(124,58,237,0.2), rgba(59,130,246,0.2))',
            flexShrink: 0,
          }}
        />
        <div style={{ overflow: 'hidden' }}>
          <p style={{
            fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>
            {book.title}
          </p>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{book.category}</p>
        </div>
      </div>
    </Link>
  );
}

/* ===== Main Detail Page ===== */
export default function BookDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const [book, setBook] = useState<Book | null>(null);
  const [recs, setRecs] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const [b, r] = await Promise.all([fetchBook(id), fetchRecommendations(id)]);
        setBook(b);
        setRecs(r);
      } catch {
        setError('Failed to load book details.');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
        <div className="spinner" />
      </div>
    );
  }
  if (error || !book) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0' }}>
        <p style={{ color: 'var(--accent-rose)' }}>{error || 'Book not found'}</p>
        <Link href="/" className="btn-secondary" style={{ marginTop: '16px', display: 'inline-block', textDecoration: 'none' }}>
          ← Back to Dashboard
        </Link>
      </div>
    );
  }

  const sentimentColor: Record<string, string> = {
    Positive: 'var(--accent-emerald)',
    Negative: 'var(--accent-rose)',
    Mixed: 'var(--accent-amber)',
    Neutral: 'var(--accent-blue)',
  };

  return (
    <div className="animate-fade-in">
      {/* Back button */}
      <Link
        href="/"
        style={{
          display: 'inline-flex', alignItems: 'center', gap: '6px',
          color: 'var(--text-secondary)', textDecoration: 'none',
          fontSize: '0.875rem', marginBottom: '24px',
          transition: 'color 0.2s',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--text-primary)'; }}
        onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-secondary)'; }}
      >
        ← Back to Dashboard
      </Link>

      {/* Hero */}
      <div
        className="glass-card"
        style={{
          display: 'flex',
          gap: '32px',
          padding: '32px',
          marginBottom: '24px',
          flexWrap: 'wrap',
        }}
      >
        {/* Cover */}
        <div
          style={{
            width: '200px',
            height: '280px',
            borderRadius: 'var(--radius-md)',
            background: book.cover_image_url
              ? `url(${book.cover_image_url}) center/cover`
              : 'linear-gradient(135deg, rgba(124,58,237,0.2), rgba(59,130,246,0.2))',
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {!book.cover_image_url && <span style={{ fontSize: '4rem', opacity: 0.3 }}>📖</span>}
        </div>

        {/* Metadata */}
        <div style={{ flex: 1, minWidth: '280px' }}>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '8px', letterSpacing: '-0.02em' }}>
            {book.title}
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginBottom: '16px' }}>
            by {book.author}
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
            <Stars rating={book.rating} />
            <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
              {book.rating}/5 · {book.num_reviews} reviews
            </span>
          </div>

          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
            {book.category && <span className="badge badge-blue">{book.category}</span>}
            {book.genre && <span className="badge badge-violet">{book.genre}</span>}
            {book.sentiment && (
              <span className="badge" style={{
                background: `${sentimentColor[book.sentiment] || 'var(--accent-blue)'}20`,
                color: sentimentColor[book.sentiment] || 'var(--accent-blue)',
              }}>
                {book.sentiment}
              </span>
            )}
          </div>

          {book.price != null && (
            <p style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-emerald)', marginBottom: '12px' }}>
              £{Number(book.price).toFixed(2)}
            </p>
          )}

          <div style={{ display: 'flex', gap: '12px', marginBottom: '8px', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            {book.availability && <span>📦 {book.availability}</span>}
            {book.upc && <span>🔖 UPC: {book.upc}</span>}
          </div>

          {book.book_url && (
            <a
              href={book.book_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary"
              style={{ display: 'inline-block', textDecoration: 'none', marginTop: '8px', fontSize: '0.8125rem' }}
            >
              🔗 View Source
            </a>
          )}
        </div>
      </div>

      {/* AI Insights */}
      <h2
        className="gradient-text"
        style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '16px' }}
      >
        AI Insights
      </h2>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '16px',
          marginBottom: '32px',
        }}
      >
        <InsightCard icon="📝" title="Summary" content={book.summary} color="var(--accent-violet)" />
        <InsightCard icon="🏷️" title="Genre" content={book.genre} color="var(--accent-blue)" />
        <InsightCard
          icon="💭"
          title="Sentiment"
          content={`Tone: ${book.sentiment || 'Not analyzed'}`}
          color={sentimentColor[book.sentiment] || 'var(--accent-blue)'}
        />
      </div>

      {/* Description */}
      {book.description && (
        <>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '12px' }}>Description</h2>
          <div
            className="glass-card"
            style={{ padding: '24px', marginBottom: '32px', lineHeight: 1.7, color: 'var(--text-secondary)' }}
          >
            {book.description}
          </div>
        </>
      )}

      {/* Recommendations */}
      {recs.length > 0 && (
        <>
          <h2
            className="gradient-text"
            style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '16px' }}
          >
            📚 If you like this, you&apos;ll also enjoy
          </h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: '12px',
              marginBottom: '40px',
            }}
          >
            {recs.map((r) => <RecCard key={r.id} book={r} />)}
          </div>
        </>
      )}
    </div>
  );
}
