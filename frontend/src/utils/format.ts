export function formatDate(dateStr: string | null): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export function formatDateRange(start: string | null, end: string | null): string {
  if (!start && !end) return '';
  if (start && !end) return `с ${formatDate(start)}`;
  if (!start && end) return `до ${formatDate(end)}`;
  return `${formatDate(start)} — ${formatDate(end)}`;
}

export function formatPrice(min: number | null, max: number | null, currency = 'RUB'): string {
  const currSymbol = currency === 'RUB' ? '₽' : currency;
  if (min !== null && max !== null && min !== max) {
    return `${Math.round(min)} — ${Math.round(max)} ${currSymbol}`;
  }
  if (min !== null) {
    return `от ${Math.round(min)} ${currSymbol}`;
  }
  if (max !== null) {
    return `до ${Math.round(max)} ${currSymbol}`;
  }
  return '';
}

export function getEventTypeEmoji(eventType: string): string {
  const emojis: Record<string, string> = {
    exhibition: '🎨',
    theatre: '🎭',
    cinema: '🎬',
    museum: '🏛',
    concert: '🎵',
    festival: '🎪',
    lecture: '📚',
  };
  return emojis[eventType] || '📌';
}

export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trimEnd() + '…';
}
