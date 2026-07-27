import { Category } from '@/types';

interface CategoryPickerProps {
  categories: Category[];
  selectedIds: number[];
  onToggle: (id: number) => void;
  maxSelections?: number;
}

export default function CategoryPicker({ categories, selectedIds, onToggle, maxSelections = 10 }: CategoryPickerProps) {
  const isFull = selectedIds.length >= maxSelections;

  return (
    <div className="picker-grid">
      {categories.map(cat => {
        const isSelected = selectedIds.includes(cat.id);
        const disabled = !isSelected && isFull;

        return (
          <button
            key={cat.id}
            className={`picker-chip ${isSelected ? 'picker-chip-selected' : ''} ${disabled ? 'picker-chip-disabled' : ''}`}
            onClick={() => !disabled && onToggle(cat.id)}
            disabled={disabled}
          >
            {cat.emoji || '📌'} {cat.name_ru}
            {isSelected && ' ✓'}
          </button>
        );
      })}
    </div>
  );
}
