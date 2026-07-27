import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFeed } from '@/hooks/useFeed';
import { useTMA } from '@/hooks/useTMA';
import EventCard from '@/components/EventCard';

export default function Feed() {
  const navigate = useNavigate();
  const { tg } = useTMA();
  const { events, loading, error, total, loadMore } = useFeed();

  useEffect(() => {
    tg?.BackButton?.hide();
  }, [tg]);

  // Infinite scroll with Intersection Observer
  useEffect(() => {
    if (loading || !events.length) return;

    const observer = new IntersectionObserver(
      entries => {
        if (entries[0]?.isIntersecting) {
          loadMore();
        }
      },
      { threshold: 0.5 },
    );

    const sentinel = document.getElementById('feed-sentinel');
    if (sentinel) observer.observe(sentinel);

    return () => observer.disconnect();
  }, [loading, events.length, loadMore]);

  if (error) {
    return (
      <div className="page">
        <div className="error-state">
          <p>❌ {error}</p>
          <button onClick={() => window.location.reload()} className="retry-button">
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page-header">
        <h1>📰 Лента событий</h1>
        {total > 0 && <span className="page-subtitle">{total} событий</span>}
      </header>

      {loading && events.length === 0 ? (
        <div className="loading-state">
          <div className="spinner" />
          <p>Загружаем события…</p>
        </div>
      ) : events.length === 0 ? (
        <div className="empty-state">
          <p>🏛 Событий пока нет</p>
          <p className="empty-state-hint">
            Настройте города и категории в разделе «Настройки»
          </p>
        </div>
      ) : (
        <>
          <div className="feed-list">
            {events.map(event => (
              <EventCard
                key={event.id}
                event={event}
                onClick={id => navigate(`/event/${id}`)}
              />
            ))}
          </div>

          <div id="feed-sentinel" className="feed-sentinel">
            {loading && <div className="spinner" />}
          </div>
        </>
      )}
    </div>
  );
}
