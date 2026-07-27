import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '@/api/client';
import { useTMA } from '@/hooks/useTMA';
import { EventDetail } from '@/types';
import { formatDateRange, formatPrice, getEventTypeEmoji } from '@/utils/format';
import TicketButton from '@/components/TicketButton';

export default function EventPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { tg } = useTMA();
  const [event, setEvent] = useState<EventDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    tg?.BackButton?.show();

    if (!id) return;
    setLoading(true);
    api.getEvent(Number(id))
      .then(setEvent)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [id, tg]);

  if (loading) {
    return (
      <div className="page">
        <div className="loading-state">
          <div className="spinner" />
          <p>Загружаем событие…</p>
        </div>
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="page">
        <div className="error-state">
          <p>❌ {error || 'Событие не найдено'}</p>
          <button onClick={() => navigate(-1)} className="retry-button">Назад</button>
        </div>
      </div>
    );
  }

  const emoji = getEventTypeEmoji(event.event_type);
  const dateStr = formatDateRange(event.start_date, event.end_date);
  const priceStr = formatPrice(event.price_min, event.price_max);

  return (
    <div className="page">
      {event.image_url && (
        <div className="event-detail-image">
          <img src={event.image_url} alt={event.title} />
        </div>
      )}

      <div className="event-detail">
        <div className="event-detail-tags">
          {event.category_names.map((cat, i) => (
            <span key={i} className="event-card-category-tag">{cat}</span>
          ))}
        </div>

        <h1 className="event-detail-title">{emoji} {event.title}</h1>

        {event.venue_name && (
          <p className="event-detail-row">📍 <strong>{event.venue_name}</strong></p>
        )}
        {event.venue_address && (
          <p className="event-detail-row event-detail-address">{event.venue_address}</p>
        )}
        {dateStr && (
          <p className="event-detail-row">🗓 {dateStr}</p>
        )}
        {priceStr && (
          <p className="event-detail-row">💰 {priceStr}</p>
        )}

        <div className="event-detail-section">
          <h2>О событии</h2>
          <p className="event-detail-description">{event.description || event.short_description || 'Описание отсутствует'}</p>
        </div>

        <div className="event-detail-actions">
          {event.ticket_url && <TicketButton url={event.ticket_url} provider={event.ticket_provider} />}
          {event.url && (
            <button
              className="link-button"
              onClick={() => {
                const tg = (window as any).Telegram?.WebApp;
                tg?.openLink ? tg.openLink(event.url!) : window.open(event.url!, '_blank');
              }}
            >
              🔗 Подробнее на сайте
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
