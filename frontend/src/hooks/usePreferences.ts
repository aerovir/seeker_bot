import { useState, useEffect, useCallback } from 'react';
import { api } from '@/api/client';
import { City, Category, Preferences, PreferencesUpdate } from '@/types';

interface UsePreferencesReturn {
  preferences: Preferences | null;
  cities: City[];
  categories: Category[];
  loading: boolean;
  error: string | null;
  updatePreferences: (data: PreferencesUpdate) => Promise<void>;
}

export function usePreferences(): UsePreferencesReturn {
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [cities, setCities] = useState<City[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [citiesData, categoriesData] = await Promise.all([
        api.getCities(),
        api.getCategories(),
      ]);
      setCities(citiesData);
      setCategories(categoriesData);

      try {
        const prefs = await api.getPreferences();
        setPreferences(prefs);
      } catch {
        // User not registered yet — that's ok
        setPreferences(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const updatePreferences = useCallback(async (data: PreferencesUpdate) => {
    setLoading(true);
    setError(null);
    try {
      const updated = await api.updatePreferences(data);
      setPreferences(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update preferences');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { preferences, cities, categories, loading, error, updatePreferences };
}
