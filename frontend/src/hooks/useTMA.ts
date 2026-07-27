import { useEffect, useState } from 'react';

interface TMAContext {
  tg: any;
  user: {
    id: number;
    username?: string;
    first_name?: string;
    last_name?: string;
  } | null;
  ready: boolean;
  colorScheme: 'light' | 'dark';
}

export function useTMA(): TMAContext {
  const [context, setContext] = useState<TMAContext>({
    tg: null,
    user: null,
    ready: false,
    colorScheme: 'light',
  });

  useEffect(() => {
    const tg = (window as any).Telegram?.WebApp;
    if (!tg) {
      setContext(prev => ({ ...prev, ready: true }));
      return;
    }

    tg.ready();
    tg.expand();

    setContext({
      tg,
      user: tg.initDataUnsafe?.user || null,
      ready: true,
      colorScheme: tg.colorScheme || 'light',
    });

    // Listen for theme changes
    tg.onEvent('themeChanged', () => {
      setContext(prev => ({
        ...prev,
        colorScheme: tg.colorScheme || 'light',
      }));
    });

    // Configure back button
    tg.BackButton?.onClick(() => {
      window.history.back();
    });

    return () => {
      tg.offEvent('themeChanged');
    };
  }, []);

  return context;
}

export function showAlert(message: string): void {
  const tg = (window as any).Telegram?.WebApp;
  if (tg?.showAlert) {
    tg.showAlert(message);
  } else {
    alert(message);
  }
}

export function showConfirm(message: string): Promise<boolean> {
  return new Promise(resolve => {
    const tg = (window as any).Telegram?.WebApp;
    if (tg?.showConfirm) {
      tg.showConfirm(message, (confirmed: boolean) => resolve(confirmed));
    } else {
      resolve(window.confirm(message));
    }
  });
}
