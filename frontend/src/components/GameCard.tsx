import { Link } from 'react-router-dom';
import { Trash2, Users, Clock, Gamepad2 } from 'lucide-react';
import type { Game } from '../types';

interface GameCardProps {
  game: Game;
  onDelete?: (id: string) => void;
}

export function GameCard({ game, onDelete }: GameCardProps) {
  const rules = game.structured_rules;

  return (
    <div className="card group hover:border-brand-500/50 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <Link
            to={`/game/${game.id}`}
            className="text-lg font-display font-semibold text-white hover:text-brand-400 transition-colors"
          >
            {game.name}
          </Link>
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
            {rules && (
              <>
                <span className="flex items-center gap-1">
                  <Users size={14} />
                  {rules.min_players}–{rules.max_players} players
                </span>
                {rules.estimated_duration_minutes && (
                  <span className="flex items-center gap-1">
                    <Clock size={14} />
                    {rules.estimated_duration_minutes} min
                  </span>
                )}
              </>
            )}
            <span className={`badge ${game.source === 'ocr' ? 'badge-info' : 'badge-success'}`}>
              {game.source === 'ocr' ? 'OCR' : 'Search'}
            </span>
          </div>
          {rules?.summary && (
            <p className="mt-3 text-sm text-gray-300 line-clamp-2">{rules.summary}</p>
          )}
        </div>
        <div className="flex items-center gap-2 ml-4">
          <Link
            to={`/game/${game.id}`}
            className="p-2 rounded-lg hover:bg-game-border text-gray-400 hover:text-white transition-colors"
            title="Play"
          >
            <Gamepad2 size={18} />
          </Link>
          {onDelete && (
            <button
              onClick={() => onDelete(game.id)}
              className="p-2 rounded-lg hover:bg-red-900/30 text-gray-400 hover:text-red-400 transition-colors"
              title="Delete"
            >
              <Trash2 size={18} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
