import { Mic, MicOff, Loader } from 'lucide-react';
import { useVoice } from '../hooks/useVoice';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
}

export function VoiceInput({ onTranscript }: VoiceInputProps) {
  const { recording, transcribing, startRecording, stopRecording } = useVoice();

  const handleToggle = async () => {
    if (recording) {
      const text = await stopRecording();
      if (text) {
        onTranscript(text);
      }
    } else {
      await startRecording();
    }
  };

  return (
    <button
      onClick={handleToggle}
      disabled={transcribing}
      className={`p-2.5 rounded-lg transition-all duration-200 ${
        recording
          ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
          : transcribing
            ? 'bg-game-border text-gray-400 cursor-wait'
            : 'bg-game-card hover:bg-game-border text-gray-400 hover:text-white border border-game-border'
      }`}
      title={recording ? 'Stop recording' : transcribing ? 'Transcribing...' : 'Start voice input'}
    >
      {transcribing ? (
        <Loader size={20} className="animate-spin" />
      ) : recording ? (
        <MicOff size={20} />
      ) : (
        <Mic size={20} />
      )}
    </button>
  );
}
