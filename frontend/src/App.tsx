import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useTMA } from '@/hooks/useTMA';
import Navigation from '@/components/Navigation';
import Feed from '@/pages/Feed';
import EventDetail from '@/pages/EventDetail';
import Settings from '@/pages/Settings';
import Search from '@/pages/Search';

function AppContent() {
  const { ready, colorScheme } = useTMA();

  if (!ready) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
      </div>
    );
  }

  const isDark = colorScheme === 'dark';

  return (
    <div className={`app ${isDark ? 'app-dark' : 'app-light'}`}>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Feed />} />
          <Route path="/event/:id" element={<EventDetail />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/search" element={<Search />} />
        </Routes>
      </main>
      <Navigation />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
