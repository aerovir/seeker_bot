export interface Event {
  id: number;
  title: string;
  description: string | null;
  short_description: string | null;
  url: string | null;
  image_url: string | null;
  event_type: string;
  start_date: string | null;
  end_date: string | null;
  is_multiday: boolean;
  venue_name: string | null;
  venue_address: string | null;
  price_min: number | null;
  price_max: number | null;
  currency: string;
  ticket_url: string | null;
  ticket_provider: string | null;
  is_featured: boolean;
  city_names: string[];
  category_names: string[];
}

export interface EventDetail extends Event {
  raw_data: Record<string, unknown> | null;
  source_url: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface FeedResponse {
  items: Event[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface City {
  id: number;
  slug: string;
  name_ru: string;
  name_en: string | null;
  region: string | null;
}

export interface Category {
  id: number;
  slug: string;
  name_ru: string;
  name_en: string | null;
  emoji: string | null;
}

export interface PreferencesUpdate {
  city_ids: number[];
  category_ids: number[];
}

export interface Preferences {
  city_ids: number[];
  city_names: string[];
  category_ids: number[];
  category_names: string[];
  notification_frequency: string;
}
