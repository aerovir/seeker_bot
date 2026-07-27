interface TicketButtonProps {
  url: string;
  provider: string | null;
}

const PROVIDER_LABELS: Record<string, string> = {
  yandex_afisha: 'Яндекс Афиша',
  kassir: 'Кассир.ру',
  ticketland: 'Ticketland',
};

export default function TicketButton({ url, provider }: TicketButtonProps) {
  const label = provider ? (PROVIDER_LABELS[provider] || provider) : 'Купить билеты';

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();

    const tg = (window as any).Telegram?.WebApp;
    if (tg?.openLink) {
      tg.openLink(url);
    } else {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <button className="ticket-button" onClick={handleClick}>
      🎫 {label}
    </button>
  );
}
