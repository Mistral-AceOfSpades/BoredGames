import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useAppStore } from '../store/gameStore';
import { GameCard } from '../components/GameCard';
import type { Game } from '../types';
import { Loader, Inbox } from 'lucide-react';

export function GamesListPage() {
  const { games, setGames, removeGame } = useAppStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.games
      .list()
      .then(setGames)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [setGames]);

  const handleDelete = async (id: string) => {
    try {
      await api.games.delete(id);
      removeGame(id);
    } catch {
      // ignore
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader className="animate-spin text-brand-400" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="font-display text-3xl font-bold text-white">My Games</h1>

      {games.length === 0 ? (
        <div className="card text-center py-16">
          <Inbox className="mx-auto h-12 w-12 text-gray-600 mb-4" />
          <p className="text-gray-400 text-lg">No games yet</p>
          <p className="text-gray-500 text-sm mt-1">
            Search for a game or upload a rulebook to get started.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {games.map((game: Game) => (
            <GameCard key={game.id} game={game} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}
