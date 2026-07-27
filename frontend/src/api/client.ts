import { FeedResponse, EventDetail, City, Category, Preferences, PreferencesUpdate } from '@/types';

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

function getAuthHeaders(): Record<string, string> {
  const initData = (window as any).Telegram?.WebApp?.initData;
  if (initData) {
    return { Authorization: `tma ${initData}` };
  }
  return {};
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Public endpoints
  getFeed(page = 1, pageSize = 20): Promise<FeedResponse> {
    return request<FeedResponse>(`/feed?page=${page}&page_size=${pageSize}`);
  },

  getEvents(params?: {
    page?: number;
    page_size?: number;
    city_id?: number;
    category_id?: number;
    event_type?: string;
  }): Promise<FeedResponse> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) searchParams.set(key, String(value));
      });
    }
    return request<FeedResponse>(`/events?${searchParams}`);
  },

  getEvent(id: number): Promise<EventDetail> {
    return request<EventDetail>(`/events/${id}`);
  },

  getCities(): Promise<City[]> {
    return request<City[]>('/cities');
  },

  getCategories(): Promise<Category[]> {
    return request<Category[]>('/categories');
  },

  // Authenticated endpoints
  getPreferences(): Promise<Preferences> {
    return request<Preferences>('/preferences/');
  },

  updatePreferences(data: PreferencesUpdate): Promise<Preferences> {
    return request<Preferences>('/preferences/', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
};
