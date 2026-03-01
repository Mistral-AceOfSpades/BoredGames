import { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, Play, Pause, SkipForward, AlertTriangle,
  Scale, Users, Loader, Send
} from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/gameStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { ChatMessage } from '../components/ChatMessage';
import { VoiceInput } from '../components/VoiceInput';
import type { Game, GameSession } from '../types';

export function ModeratePage() {
  const { id } = useParams<{ id: string }>();
  const { currentGame, setCurrentGame, currentSession, setCurrentSession } = useAppStore();
  const [loading, setLoading] = useState(true);
  const [playerNames, setPlayerNames] = useState('');
  const [setupPhase, setSetupPhase] = useState(true);
  const [actionInput, setActionInput] = useState('');
  const [disputeInput, setDisputeInput] = useState('');
  const [showDispute, setShowDispute] = useState(false);
  const [messages, setMessages] = useState<{ role: string; content: string; citations?: string[] }[]>([]);
  const [processing, setProcessing] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const { messages: wsMessages, connected, send } = useWebSocket(currentSession?.id ?? null);

  useEffect(() => {
    if (!id) return;
    api.games
      .get(id)
      .then((game) => {
        setCurrentGame(game);
        setSetupPhase(true);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id, setCurrentGame]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleStartSession = async () => {
    if (!id || !playerNames.trim()) return;
    const players = playerNames.split(',').map((n) => n.trim()).filter(Boolean);
    if (players.length < 2) return;

    setProcessing(true);
    try {
      const session = await api.games.createSession(id, players);
      setCurrentSession(session);
      setSetupPhase(false);
      setMessages([
        {
          role: 'system',
          content: `Game session started! Players: ${players.join(', ')}. It's ${players[0]}'s turn.`,
        },
      ]);
    } catch (err) {
      setMessages([{ role: 'system', content: 'Failed to create session. Please try again.' }]);
    } finally {
      setProcessing(false);
    }
  };

  const handleAdvanceTurn = async () => {
    if (!currentSession) return;
    setProcessing(true);
    try {
      const result = await api.moderate.advanceTurn(currentSession.id);
      setCurrentSession({
        ...currentSession,
        current_turn: result.current_turn,
      });
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `**${result.current_player}'s turn** (Round ${result.round})\n\n${result.guidance}`,
        },
      ]);
    } catch {
      setMessages((prev) => [...prev, { role: 'system', content: 'Failed to advance turn.' }]);
    } finally {
      setProcessing(false);
    }
  };

  const handleValidateMove = async (action?: string) => {
    const finalAction = action || actionInput;
    if (!currentSession || !finalAction.trim()) return;

    const currentPlayer = currentSession.turn_order?.[currentSession.current_turn] || 'Unknown';
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: `${currentPlayer}: ${finalAction}` },
    ]);
    setActionInput('');
    setProcessing(true);

    try {
      const result = await api.moderate.validateMove(currentSession.id, currentPlayer, finalAction);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.valid
            ? `✅ **Valid move.** ${result.reason}`
            : `❌ **Invalid move.** ${result.reason}\n\n📖 *Rule: ${result.rule_reference}*${result.suggestion ? `\n\n💡 Suggestion: ${result.suggestion}` : ''}`,
        },
      ]);
    } catch {
      setMessages((prev) => [...prev, { role: 'system', content: 'Failed to validate move.' }]);
    } finally {
      setProcessing(false);
    }
  };

  const handleDispute = async () => {
    if (!currentSession || !currentGame || !disputeInput.trim()) return;
    setMessages((prev) => [...prev, { role: 'user', content: `⚖️ Dispute: ${disputeInput}` }]);
    setProcessing(true);
    const desc = disputeInput;
    setDisputeInput('');

    try {
      const result = await api.moderate.dispute(currentGame.id, currentSession.id, desc);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.flagged
            ? result.resolution
            : `⚖️ **Ruling** (${result.interpretation_level}, ${result.confidence} confidence):\n\n${result.resolution}`,
          citations: result.citations,
        },
      ]);
    } catch {
      setMessages((prev) => [...prev, { role: 'system', content: 'Failed to resolve dispute.' }]);
    } finally {
      setProcessing(false);
      setShowDispute(false);
    }
  };

  const handleCheckWin = async () => {
    if (!currentSession) return;
    setProcessing(true);
    try {
      const result = await api.moderate.checkWin(currentSession.id);
      if (result.game_over) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `🏆 **Game Over!** ${result.winner} wins!` },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: 'No winner yet. The game continues!' },
        ]);
      }
    } catch {
      setMessages((prev) => [...prev, { role: 'system', content: 'Failed to check win condition.' }]);
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader className="animate-spin text-brand-400" size={32} />
      </div>
    );
  }

  if (!currentGame) {
    return (
      <div className="card text-center py-16">
        <p className="text-gray-400 text-lg">Game not found</p>
      </div>
    );
  }

  // Setup phase
  if (setupPhase) {
    return (
      <div className="max-w-lg mx-auto space-y-6">
        <div className="flex items-center gap-4">
          <Link to={`/game/${currentGame.id}`} className="text-gray-400 hover:text-white">
            <ArrowLeft size={20} />
          </Link>
          <h1 className="font-display text-2xl font-bold text-white">
            Moderate: {currentGame.name}
          </h1>
        </div>

        <div className="card space-y-4">
          <h2 className="font-display text-lg font-semibold text-white flex items-center gap-2">
            <Users size={20} className="text-brand-400" />
            Player Setup
          </h2>
          <p className="text-sm text-gray-400">Enter player names separated by commas.</p>
          <input
            type="text"
            value={playerNames}
            onChange={(e) => setPlayerNames(e.target.value)}
            placeholder="Alice, Bob, Charlie"
            className="input"
          />
          <button
            onClick={handleStartSession}
            disabled={processing || !playerNames.includes(',')}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {processing ? (
              <Loader size={16} className="animate-spin" />
            ) : (
              <Play size={16} />
            )}
            Start Game Session
          </button>
        </div>
      </div>
    );
  }

  // Active moderation
  const currentPlayer = currentSession?.turn_order?.[currentSession?.current_turn ?? 0] || 'Unknown';

  return (
    <div className="space-y-4">
      {/* Header bar */}
      <div className="card py-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <Link to={`/game/${currentGame.id}`} className="text-gray-400 hover:text-white">
            <ArrowLeft size={20} />
          </Link>
          <h2 className="font-display font-semibold text-white">{currentGame.name}</h2>
          <span className="badge-info">
            Turn: {currentPlayer}
          </span>
        </div>
        <div className="flex gap-2">
          <button onClick={handleAdvanceTurn} disabled={processing} className="btn-secondary text-sm py-1.5 flex items-center gap-1">
            <SkipForward size={14} /> Next Turn
          </button>
          <button onClick={() => setShowDispute(!showDispute)} className="btn-secondary text-sm py-1.5 flex items-center gap-1">
            <Scale size={14} /> Dispute
          </button>
          <button onClick={handleCheckWin} disabled={processing} className="btn-secondary text-sm py-1.5 flex items-center gap-1">
            🏆 Check Win
          </button>
        </div>
      </div>

      {/* Dispute input */}
      {showDispute && (
        <div className="card border-yellow-800 bg-yellow-900/10">
          <h3 className="text-white font-medium mb-2 flex items-center gap-2">
            <AlertTriangle size={16} className="text-yellow-400" />
            Dispute Resolution
          </h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={disputeInput}
              onChange={(e) => setDisputeInput(e.target.value)}
              placeholder="Describe the dispute..."
              className="input flex-1"
            />
            <button onClick={handleDispute} disabled={processing || !disputeInput.trim()} className="btn-primary">
              Submit
            </button>
          </div>
        </div>
      )}

      {/* Chat / moderation log */}
      <div className="card flex flex-col" style={{ height: '55vh' }}>
        <div className="flex-1 overflow-y-auto space-y-4 p-4">
          {messages.map((msg, i) => (
            <ChatMessage
              key={i}
              role={msg.role as 'user' | 'assistant' | 'system'}
              content={msg.content}
              citations={msg.citations}
            />
          ))}
          {processing && (
            <div className="flex items-center gap-2 text-gray-400">
              <Loader size={16} className="animate-spin" />
              <span className="text-sm">Processing...</span>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Action input */}
        <div className="border-t border-game-border p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleValidateMove();
            }}
            className="flex gap-2"
          >
            <input
              type="text"
              value={actionInput}
              onChange={(e) => setActionInput(e.target.value)}
              placeholder={`${currentPlayer}'s action...`}
              className="input flex-1"
              disabled={processing}
            />
            <VoiceInput onTranscript={(text) => handleValidateMove(text)} />
            <button type="submit" disabled={processing || !actionInput.trim()} className="btn-primary p-2.5">
              <Send size={18} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
