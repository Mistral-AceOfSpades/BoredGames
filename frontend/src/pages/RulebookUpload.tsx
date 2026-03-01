import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileUpload } from '../components/FileUpload';
import { api } from '../api/client';
import { useAppStore } from '../store/gameStore';

export function RulebookUploadPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [urlMode, setUrlMode] = useState(false);
  const [url, setUrl] = useState('');
  const navigate = useNavigate();
  const addGame = useAppStore((s) => s.addGame);

  const handleFileSelect = async (file: File) => {
    setLoading(true);
    setError('');
    try {
      const game = await api.ocr.upload(file);
      addGame(game);
      navigate(`/game/${game.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    try {
      const game = await api.ocr.fromUrl(url.trim());
      addGame(game);
      navigate(`/game/${game.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'URL processing failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="font-display text-3xl font-bold text-white mb-2">Upload Rulebook</h1>
        <p className="text-gray-400">
          Upload rulebook images or PDFs — Mistral OCR will extract and structure the rules.
        </p>
      </div>

      {/* Toggle */}
      <div className="flex justify-center gap-2">
        <button
          onClick={() => setUrlMode(false)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            !urlMode ? 'bg-brand-600 text-white' : 'bg-game-card text-gray-400 border border-game-border'
          }`}
        >
          Upload File
        </button>
        <button
          onClick={() => setUrlMode(true)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            urlMode ? 'bg-brand-600 text-white' : 'bg-game-card text-gray-400 border border-game-border'
          }`}
        >
          From URL
        </button>
      </div>

      {urlMode ? (
        <form onSubmit={handleUrlSubmit} className="space-y-4">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/rulebook.pdf"
            className="input"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !url.trim()} className="btn-primary w-full">
            {loading ? 'Processing...' : 'Process URL'}
          </button>
        </form>
      ) : (
        <FileUpload onFileSelect={handleFileSelect} loading={loading} />
      )}

      {error && (
        <div className="card border-red-800 bg-red-900/20">
          <p className="text-red-300">{error}</p>
        </div>
      )}
    </div>
  );
}
