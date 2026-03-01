import { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { BookOpen, Zap, List, Play, MessageCircle, Send, Loader, ArrowLeft } from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/gameStore';
import { ChatMessage } from '../components/ChatMessage';
import { VoiceInput } from '../components/VoiceInput';
import type { ExplanationMode, Game } from '../types';
import ReactMarkdown from 'react-markdown';

const MODES: { key: ExplanationMode; label: string; icon: typeof Zap; desc: string }[] = [
  { key: 'quick_start', label: 'Quick Start', icon: Zap, desc: '3–5 min summary' },
  { key: 'step_by_step', label: 'Step by Step', icon: List, desc: 'Detailed walkthrough' },
  { key: 'playthrough', label: 'Playthrough', icon: Play, desc: 'Simulated round' },
  { key: 'qa', label: 'Q&A', icon: MessageCircle, desc: 'Ask questions' },
];

export function ExplainPage() {
  const { id } = useParams<{ id: string }>();
  const { currentGame, setCurrentGame } = useAppStore();
  const [mode, setMode] = useState<ExplanationMode>('quick_start');
  const [explanation, setExplanation] = useState('');
  const [loading, setLoading] = useState(false);
  const [qaMessages, setQaMessages] = useState<{ role: string; content: string; citations?: string[] }[]>([]);
  const [question, setQuestion] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!id) return;
    if (!currentGame || currentGame.id !== id) {
      api.games.get(id).then(setCurrentGame).catch(() => {});
    }
  }, [id, currentGame, setCurrentGame]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [qaMessages]);

  const handleExplain = async (selectedMode: ExplanationMode) => {
    setMode(selectedMode);
    if (selectedMode === 'qa') {
      setQaMessages([]);
      return;
    }
    if (!id) return;
    setLoading(true);
    setExplanation('');
    try {
      const result = await api.explain.get(id, selectedMode);
      setExplanation(result.explanation);
    } catch (err) {
      setExplanation('Failed to generate explanation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAskQuestion = async (q?: string) => {
    const finalQ = q || question;
    if (!finalQ.trim() || !id) return;

    const userMsg = { role: 'user' as const, content: finalQ };
    setQaMessages((prev) => [...prev, userMsg]);
    setQuestion('');
    setLoading(true);

    try {
      const result = await api.explain.qa(id, finalQ);
      setQaMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.answer,
          citations: result.citations,
        },
      ]);
    } catch {
      setQaMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I could not answer that question. Please try again.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!currentGame) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader className="animate-spin text-brand-400" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to={`/game/${currentGame.id}`} className="text-gray-400 hover:text-white">
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h1 className="font-display text-2xl font-bold text-white">
            Explain: {currentGame.name}
          </h1>
          <p className="text-sm text-gray-400">Choose an explanation mode below</p>
        </div>
      </div>

      {/* Mode selector */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {MODES.map((m) => (
          <button
            key={m.key}
            onClick={() => handleExplain(m.key)}
            className={`card text-center py-4 transition-all ${
              mode === m.key
                ? 'border-brand-500 bg-brand-900/20'
                : 'hover:border-brand-500/30'
            }`}
          >
            <m.icon className={`mx-auto mb-2 ${mode === m.key ? 'text-brand-400' : 'text-gray-500'}`} size={24} />
            <p className={`font-medium text-sm ${mode === m.key ? 'text-white' : 'text-gray-300'}`}>
              {m.label}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">{m.desc}</p>
          </button>
        ))}
      </div>

      {/* Content area */}
      {mode === 'qa' ? (
        <div className="card flex flex-col" style={{ height: '60vh' }}>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 p-4">
            {qaMessages.length === 0 && (
              <div className="text-center text-gray-500 py-12">
                <MessageCircle className="mx-auto mb-3 text-gray-600" size={40} />
                <p>Ask any question about {currentGame.name}</p>
                <p className="text-sm mt-1">Use text or voice input below</p>
              </div>
            )}
            {qaMessages.map((msg, i) => (
              <ChatMessage key={i} role={msg.role as 'user' | 'assistant'} content={msg.content} citations={msg.citations} />
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-gray-400">
                <Loader size={16} className="animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-game-border p-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAskQuestion();
              }}
              className="flex gap-2"
            >
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask about the rules..."
                className="input flex-1"
                disabled={loading}
              />
              <VoiceInput onTranscript={(text) => handleAskQuestion(text)} />
              <button type="submit" disabled={loading || !question.trim()} className="btn-primary p-2.5">
                <Send size={18} />
              </button>
            </form>
          </div>
        </div>
      ) : (
        <div className="card">
          {loading ? (
            <div className="text-center py-16">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-400 mx-auto mb-4" />
              <p className="text-gray-300 font-medium">Generating explanation...</p>
              <p className="text-sm text-gray-500 mt-1">Mistral AI is preparing your {mode.replace('_', ' ')} guide</p>
            </div>
          ) : explanation ? (
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{explanation}</ReactMarkdown>
            </div>
          ) : (
            <div className="text-center py-16 text-gray-500">
              <BookOpen className="mx-auto mb-3 text-gray-600" size={40} />
              <p>Select a mode above to get started</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
