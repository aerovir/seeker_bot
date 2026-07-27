import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTMA } from '@/hooks/useTMA';
import { api } from '@/api/client';
import { Event } from '@/types';
import EventCard from '@/components/EventCard';

export default function Search() {
  const navigate = useNavigate();
  const { tg } = useTMA();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Event[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    tg?.BackButton?.hide();
  }, [tg]);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    try {
      const data = await api.getEvents({ page_size: 50 });
      // Client-side search filter (backend full-text search TBD)
      const q = query.toLowerCase();
      const filtered = data.items.filter(
        e =>
          e.title.toLowerCase().includes(q) ||
          (e.description?.toLowerCase() || '').includes(q) ||
          (e.venue_name?.toLowerCase() || '').includes(q),
      );
      setResults(filtered);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="page-header">
        <h1>🔍 Поиск</h1>
      </header>

      <div className="search-bar">
        <input
          type="text"
          className="search-input"
          placeholder="Поиск событий, мест, описаний…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
        />
        <button className="search-button" onClick={handleSearch} disabled={loading}>
          {loading ? '…' : 'Найти'}
        </button>
      </div>

      {searched && !loading && results.length === 0 && (
        <div className="empty-state">
          <p>🔍 Ничего не найдено</p>
          <p className="empty-state-hint">Попробуйте изменить запрос</p>
        </div>
      )}

      <div className="feed-list">
        {results.map(event => (
          <EventCard
            key={event.id}
            event={event}
            onClick={id => navigate(`/event/${id}`)}
          />
        ))}
      </div>
    </div>
  );
}
