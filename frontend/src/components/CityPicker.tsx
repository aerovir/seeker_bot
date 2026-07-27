import { City } from '@/types';

interface CityPickerProps {
  cities: City[];
  selectedIds: number[];
  onToggle: (id: number) => void;
  maxSelections?: number;
}

export default function CityPicker({ cities, selectedIds, onToggle, maxSelections = 5 }: CityPickerProps) {
  const isFull = selectedIds.length >= maxSelections;

  return (
    <div className="picker-grid">
      {cities.map(city => {
        const isSelected = selectedIds.includes(city.id);
        const disabled = !isSelected && isFull;

        return (
          <button
            key={city.id}
            className={`picker-chip ${isSelected ? 'picker-chip-selected' : ''} ${disabled ? 'picker-chip-disabled' : ''}`}
            onClick={() => !disabled && onToggle(city.id)}
            disabled={disabled}
          >
            🏛 {city.name_ru}
            {isSelected && ' ✓'}
          </button>
        );
      })}
    </div>
  );
}
