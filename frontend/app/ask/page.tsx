'use client';

import { useState } from 'react';
import { askQuestion } from '@/lib/api';

export default function AskPage() {
  const [input, setInput] = useState('This is the beginning of a new journey');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [latency, setLatency] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!input.trim() || loading) return;

    setLoading(true);
    setOutput('');
    setLatency(null);

    const startTime = performance.now();

    try {
      const res = await askQuestion(input);
      // Construct output text including the answer and a summary of sources
      let outText = res.answer;
      if (res.sources && res.sources.length > 0) {
        outText += '\n\n[Sources: ' + res.sources.map(s => s.title).join(', ') + ']';
      }
      setOutput(outText);
    } catch (err) {
      setOutput('Error: Could not connect to the backend or AI service.');
    } finally {
      const endTime = performance.now();
      setLatency(((endTime - startTime) / 1000).toFixed(2));
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{
      padding: '20px 0',
      minHeight: 'calc(100vh - 64px)',
    }}>
      {/* Header */}
      <div style={{ textAlign: 'center', paddingBottom: '30px' }}>
        <h1 className="gradient-text" style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '6px' }}>
          Ask About Books
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9375rem' }}>
          AI-powered Q&A using RAG over your book collection
        </p>
      </div>

      <div style={{
        display: 'flex',
        gap: '24px',
        maxWidth: '1200px',
        margin: '0 auto',
      }}>

        {/* Left Column (INP) */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="glass-card" style={{
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            minHeight: '320px',
            flex: 1
          }}>
            <div style={{
              fontSize: '0.8125rem',
              fontWeight: 700,
              color: 'var(--text-muted)',
              marginBottom: '12px',
              letterSpacing: '0.05em'
            }}>
              INP
            </div>
            <div style={{ position: 'relative', flex: 1, display: 'flex' }}>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                style={{
                  flex: 1,
                  width: '100%',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '16px',
                  resize: 'none',
                  outline: 'none',
                  fontFamily: 'var(--font-mono), Consolas, monospace',
                  fontSize: '0.9375rem',
                  lineHeight: '1.6',
                  color: 'var(--text-primary)',
                  backgroundColor: 'rgba(0, 0, 0, 0.2)',
                  transition: 'border-color 0.2s ease',
                }}
                onFocus={(e) => e.target.style.borderColor = 'var(--accent-violet)'}
                onBlur={(e) => e.target.style.borderColor = 'var(--border-subtle)'}
              />
              {/* Green icon from screenshot adapted for dark theme */}
              <div style={{
                position: 'absolute',
                bottom: '12px',
                right: '12px',
                width: '12px',
                height: '12px',
                backgroundColor: 'var(--accent-emerald)',
                borderRadius: '50%',
                boxShadow: '0 0 10px var(--accent-emerald)'
              }}></div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '16px' }}>
            <button
              className="btn-secondary"
              onClick={() => setInput('')}
              style={{ flex: 1, padding: '14px', textTransform: 'uppercase', letterSpacing: '0.05em' }}
            >
              Clear
            </button>
            <button
              className="btn-primary"
              onClick={handleSubmit}
              disabled={loading}
              style={{
                flex: 1,
                padding: '14px',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                background: 'var(--accent-amber)', // Matching the orange from screenshot but in theme
                boxShadow: loading ? 'none' : '0 4px 20px rgba(245, 158, 11, 0.3)'
              }}
            >
              {loading ? 'Processing...' : 'Submit'}
            </button>
          </div>
        </div>

        {/* Right Column (OUTPUT) */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="glass-card" style={{
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            minHeight: '320px',
            flex: 1
          }}>
            <div style={{
              fontSize: '0.8125rem',
              fontWeight: 700,
              color: 'var(--text-muted)',
              marginBottom: '12px',
              letterSpacing: '0.05em'
            }}>
              OUTPUT
            </div>
            <div style={{
              flex: 1,
              width: '100%',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '16px',
              overflowY: 'auto',
              fontFamily: 'var(--font-mono), Consolas, monospace',
              fontSize: '0.9375rem',
              lineHeight: '1.6',
              color: 'var(--text-primary)',
              backgroundColor: 'rgba(0, 0, 0, 0.2)',
              whiteSpace: 'pre-wrap'
            }}
            >
              {loading ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-secondary)' }}>
                  <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></div>
                  Processing request...
                </div>
              ) : output}
            </div>

            <div style={{ height: '24px', marginTop: '12px' }}>
              {latency !== null && (
                <div style={{
                  textAlign: 'right',
                  fontSize: '0.8125rem',
                  color: 'var(--accent-amber)',
                  fontWeight: 600
                }}>
                  Latency: {latency}s
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '16px' }}>
            <button className="btn-secondary" style={{ flex: 1, padding: '14px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Screenshot
            </button>
            <button className="btn-secondary" style={{ flex: 1, padding: '14px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Flag
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
