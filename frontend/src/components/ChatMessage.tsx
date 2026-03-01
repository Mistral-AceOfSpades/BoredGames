import ReactMarkdown from 'react-markdown';
import { Bot, User } from 'lucide-react';
import { clsx } from 'clsx';

interface ChatMessageProps {
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations?: string[];
}

export function ChatMessage({ role, content, citations }: ChatMessageProps) {
  const isUser = role === 'user';
  const isSystem = role === 'system';

  return (
    <div
      className={clsx('flex gap-3', {
        'justify-end': isUser,
      })}
    >
      {!isUser && (
        <div
          className={clsx('flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center', {
            'bg-brand-600': !isSystem,
            'bg-game-border': isSystem,
          })}
        >
          <Bot size={16} className="text-white" />
        </div>
      )}
      <div
        className={clsx('max-w-[80%] rounded-xl px-4 py-3', {
          'bg-brand-600 text-white': isUser,
          'bg-game-card border border-game-border text-gray-200': !isUser && !isSystem,
          'bg-game-border/50 text-gray-400 text-sm italic': isSystem,
        })}
      >
        <div className="prose prose-invert prose-sm max-w-none">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
        {citations && citations.length > 0 && (
          <div className="mt-2 pt-2 border-t border-white/10">
            <p className="text-xs text-gray-400 mb-1">References:</p>
            <ul className="text-xs text-gray-500 space-y-0.5">
              {citations.map((cite, i) => (
                <li key={i}>📎 {cite}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
          <User size={16} className="text-white" />
        </div>
      )}
    </div>
  );
}
