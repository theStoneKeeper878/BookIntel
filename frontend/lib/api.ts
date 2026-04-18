/**
 * API client for communicating with the Django backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface Book {
  id: number;
  title: string;
  author: string;
  rating: number;
  num_reviews: number;
  price: number | null;
  description: string;
  book_url: string;
  cover_image_url: string;
  category: string;
  genre: string;
  summary: string;
  sentiment: string;
  sentiment_score: number;
  is_processed: boolean;
  created_at: string;
  availability: string;
  upc: string;
  chunks: BookChunk[];
}

export interface BookChunk {
  id: number;
  chunk_text: string;
  chunk_index: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface AskResponse {
  answer: string;
  sources: { title: string; book_id: number; relevance: number }[];
  context_chunks: { text: string; source: string }[];
}

export interface ScrapeStatus {
  is_running: boolean;
  progress: number;
  total: number;
  current_book: string;
  error: string | null;
}

// ---------------------------------------------------------------------------
// GET Endpoints
// ---------------------------------------------------------------------------
export async function fetchBooks(params?: {
  search?: string;
  category?: string;
  genre?: string;
  ordering?: string;
  page?: number;
}): Promise<PaginatedResponse<Book>> {
  const url = new URL(`${API_BASE}/books/`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '') url.searchParams.set(k, String(v));
    });
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`Failed to fetch books: ${res.status}`);
  return res.json();
}

export async function fetchBook(id: number): Promise<Book> {
  const res = await fetch(`${API_BASE}/books/${id}/`);
  if (!res.ok) throw new Error(`Failed to fetch book: ${res.status}`);
  return res.json();
}

export async function fetchRecommendations(id: number): Promise<Book[]> {
  const res = await fetch(`${API_BASE}/books/${id}/recommendations/`);
  if (!res.ok) throw new Error(`Failed to fetch recommendations: ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// POST Endpoints
// ---------------------------------------------------------------------------
export async function scrapeBooks(maxBooks: number = 30): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/books/scrape/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ max_books: maxBooks }),
  });
  return res.json();
}

export async function getScrapeStatus(): Promise<ScrapeStatus> {
  const res = await fetch(`${API_BASE}/books/scrape-status/`);
  return res.json();
}

export async function askQuestion(question: string, topK: number = 5): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/books/ask/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK }),
  });
  if (!res.ok) throw new Error(`Failed to ask question: ${res.status}`);
  return res.json();
}

export async function uploadBook(data: Partial<Book>): Promise<Book> {
  const res = await fetch(`${API_BASE}/books/upload/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to upload book: ${res.status}`);
  return res.json();
}
