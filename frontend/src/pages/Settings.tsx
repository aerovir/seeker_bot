import { useEffect, useState, useCallback } from 'react';
import { useTMA, showAlert } from '@/hooks/useTMA';
import { usePreferences } from '@/hooks/usePreferences';
import CityPicker from '@/components/CityPicker';
import CategoryPicker from '@/components/CategoryPicker';

export default function Settings() {
  const { tg } = useTMA();
  const { preferences, cities, categories, loading, error, updatePreferences } = usePreferences();

  const [selectedCities, setSelectedCities] = useState<number[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<number[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    tg?.BackButton?.hide();
  }, [tg]);

  useEffect(() => {
    if (preferences) {
      setSelectedCities(preferences.city_ids);
      setSelectedCategories(preferences.category_ids);
    }
  }, [preferences]);

  const toggleCity = useCallback((id: number) => {
    setSelectedCities(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id],
    );
  }, []);

  const toggleCategory = useCallback((id: number) => {
    setSelectedCategories(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id],
    );
  }, []);

  const handleSave = async () => {
    if (selectedCities.length === 0) {
      showAlert('Выберите хотя бы один город');
      return;
    }
    if (selectedCategories.length === 0) {
      showAlert('Выберите хотя бы одну категорию');
      return;
    }

    setSaving(true);
    try {
      await updatePreferences({
        city_ids: selectedCities,
        category_ids: selectedCategories,
      });
      showAlert('✅ Настройки сохранены!');
    } catch (err) {
      showAlert('❌ Ошибка при сохранении');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page">
      <header className="page-header">
        <h1>⚙️ Настройки</h1>
        <p className="page-subtitle">Выберите города и категории для вашей ленты</p>
      </header>

      {error && (
        <div className="error-banner">
          <p>⚠️ {error}</p>
        </div>
      )}

      <section className="settings-section">
        <h2>🏛 Города (до 5)</h2>
        <p className="section-hint">Выберите города, события в которых вас интересуют</p>
        <CityPicker
          cities={cities}
          selectedIds={selectedCities}
          onToggle={toggleCity}
        />
        <p className="selection-count">{selectedCities.length}/5 выбрано</p>
      </section>

      <section className="settings-section">
        <h2>📌 Категории (до 10)</h2>
        <p className="section-hint">Выберите типы событий</p>
        <CategoryPicker
          categories={categories}
          selectedIds={selectedCategories}
          onToggle={toggleCategory}
        />
        <p className="selection-count">{selectedCategories.length}/10 выбрано</p>
      </section>

      <div className="settings-actions">
        <button
          className="save-button"
          onClick={handleSave}
          disabled={saving || loading}
        >
          {saving ? '💾 Сохраняем…' : '💾 Сохранить настройки'}
        </button>
      </div>
    </div>
  );
}
