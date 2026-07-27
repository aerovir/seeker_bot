import { useState, useEffect, useCallback } from 'react';
import { api } from '@/api/client';
import { Event, FeedResponse } from '@/types';

interface UseFeedReturn {
  events: Event[];
  loading: boolean;
  error: string | null;
  page: number;
  totalPages: number;
  total: number;
  loadMore: () => void;
  refresh: () => void;
}

export function useFeed(pageSize = 20): UseFeedReturn {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);

  const fetchFeed = useCallback(async (pageNum: number) => {
    setLoading(true);
    setError(null);
    try {
      const data: FeedResponse = await api.getFeed(pageNum, pageSize);
      if (pageNum === 1) {
        setEvents(data.items);
      } else {
        setEvents(prev => [...prev, ...data.items]);
      }
      setTotalPages(data.total_pages);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load feed');
    } finally {
      setLoading(false);
    }
  }, [pageSize]);

  useEffect(() => {
    fetchFeed(1);
  }, [fetchFeed]);

  const loadMore = useCallback(() => {
    if (page < totalPages && !loading) {
      const nextPage = page + 1;
      setPage(nextPage);
      fetchFeed(nextPage);
    }
  }, [page, totalPages, loading, fetchFeed]);

  const refresh = useCallback(() => {
    setPage(1);
    fetchFeed(1);
  }, [fetchFeed]);

  return { events, loading, error, page, totalPages, total, loadMore, refresh };
}
