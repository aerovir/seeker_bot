import { useLocation, useNavigate } from 'react-router-dom';
import { useTMA } from '@/hooks/useTMA';

export default function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const { colorScheme } = useTMA();

  const isDark = colorScheme === 'dark';

  const tabs = [
    { path: '/', label: 'Лента', icon: '📰' },
    { path: '/search', label: 'Поиск', icon: '🔍' },
    { path: '/settings', label: 'Настройки', icon: '⚙️' },
  ];

  return (
    <nav className={`bottom-nav ${isDark ? 'bottom-nav-dark' : ''}`}>
      {tabs.map(tab => {
        const isActive = location.pathname === tab.path;
        return (
          <button
            key={tab.path}
            className={`bottom-nav-item ${isActive ? 'bottom-nav-item-active' : ''}`}
            onClick={() => navigate(tab.path)}
          >
            <span className="bottom-nav-icon">{tab.icon}</span>
            <span className="bottom-nav-label">{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
