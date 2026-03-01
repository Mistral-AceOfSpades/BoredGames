import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { HomePage } from './pages/Home';
import { GameSearchPage } from './pages/GameSearch';
import { RulebookUploadPage } from './pages/RulebookUpload';
import { GamesListPage } from './pages/GamesList';
import { GameViewPage } from './pages/GameView';
import { ExplainPage } from './pages/Explain';
import { ModeratePage } from './pages/Moderate';

export default function App() {
  return (
    <BrowserRouter basename="/BoredGames">
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<GameSearchPage />} />
          <Route path="/upload" element={<RulebookUploadPage />} />
          <Route path="/games" element={<GamesListPage />} />
          <Route path="/game/:id" element={<GameViewPage />} />
          <Route path="/explain/:id" element={<ExplainPage />} />
          <Route path="/moderate/:id" element={<ModeratePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
