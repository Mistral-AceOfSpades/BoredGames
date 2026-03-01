import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Loader, Sparkles } from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/gameStore';

export function GameSearchPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const addGame = useAppStore((s) => s.addGame);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');

    try {
      const game = await api.games.search(query.trim());
      addGame(game);
      navigate(`/game/${game.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="font-display text-3xl font-bold text-white mb-2">Find a Board Game</h1>
        <p className="text-gray-400">
          Enter a game name and AI will retrieve and structure the complete rules.
        </p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter board game name... e.g. Catan, Monopoly, Chess"
            className="input pl-11"
            disabled={loading}
            autoFocus
          />
        </div>
        <button type="submit" disabled={loading || !query.trim()} className="btn-primary whitespace-nowrap">
          {loading ? (
            <>
              <Loader size={16} className="animate-spin inline mr-2" />
              Searching...
            </>
          ) : (
            'Search'
          )}
        </button>
      </form>

      {error && (
        <div className="card border-red-800 bg-red-900/20">
          <p className="text-red-300">{error}</p>
        </div>
      )}

      {loading && (
        <div className="card text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-400 mx-auto mb-4" />
          <p className="text-gray-300 font-medium">Retrieving game rules...</p>
          <p className="text-sm text-gray-500 mt-1">
            Mistral AI is searching, validating, and structuring the rules
          </p>
        </div>
      )}

      {/* Popular games suggestions */}
      {!loading && !error && (
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Popular Games</h3>
          <div className="flex flex-wrap gap-2">
            {['Catan', 'Monopoly', 'Chess', 'Ticket to Ride', 'Uno', 'Scrabble', 'Risk', 'Clue', 'Pandemic', 'Codenames'].map(
              (name) => (
                <button
                  key={name}
                  onClick={() => setQuery(name)}
                  className="px-4 py-2 rounded-full bg-game-card border border-game-border text-sm text-gray-300
                             hover:border-brand-500/50 hover:text-white transition-colors flex items-center gap-1.5"
                >
                  <Sparkles size={14} className="text-brand-400" />
                  {name}
                </button>
              ),
            )}
          </div>
        </div>
      )}
    </div>
  );
}
