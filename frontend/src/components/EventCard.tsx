import { Event } from '@/types';
import { formatDateRange, formatPrice, getEventTypeEmoji, truncate } from '@/utils/format';
import TicketButton from './TicketButton';

interface EventCardProps {
  event: Event;
  onClick: (id: number) => void;
}

export default function EventCard({ event, onClick }: EventCardProps) {
  const dateStr = formatDateRange(event.start_date, event.end_date);
  const priceStr = formatPrice(event.price_min, event.price_max);
  const emoji = getEventTypeEmoji(event.event_type);

  return (
    <div
      className="event-card"
      onClick={() => onClick(event.id)}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && onClick(event.id)}
    >
      {event.image_url && (
        <div className="event-card-image">
          <img
            src={event.image_url}
            alt={event.title}
            loading="lazy"
            onError={e => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        </div>
      )}
      <div className="event-card-content">
        <div className="event-card-categories">
          {event.category_names.slice(0, 2).map((cat, i) => (
            <span key={i} className="event-card-category-tag">{cat}</span>
          ))}
        </div>
        <h3 className="event-card-title">
          {emoji} {truncate(event.title, 80)}
        </h3>
        {event.venue_name && (
          <p className="event-card-venue">📍 {event.venue_name}</p>
        )}
        {dateStr && (
          <p className="event-card-date">🗓 {dateStr}</p>
        )}
        {priceStr && (
          <p className="event-card-price">💰 {priceStr}</p>
        )}
        {event.short_description && (
          <p className="event-card-desc">{truncate(event.short_description, 120)}</p>
        )}
        <div className="event-card-footer">
          <div className="event-card-cities">
            {event.city_names.map((city, i) => (
              <span key={i} className="event-card-city-tag">{city}</span>
            ))}
          </div>
          {event.ticket_url && <TicketButton url={event.ticket_url} provider={event.ticket_provider} />}
        </div>
      </div>
    </div>
  );
}
