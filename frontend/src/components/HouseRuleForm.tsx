import { useState } from 'react';
import { AlertTriangle, CheckCircle, XCircle, Loader } from 'lucide-react';
import { api } from '../api/client';
import type { HouseRuleValidation } from '../types';
import { VoiceInput } from './VoiceInput';

interface HouseRuleFormProps {
  gameId: string;
  onRuleAdded?: () => void;
}

export function HouseRuleForm({ gameId, onRuleAdded }: HouseRuleFormProps) {
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [validation, setValidation] = useState<HouseRuleValidation | null>(null);
  const [error, setError] = useState('');

  const handleValidate = async () => {
    if (!description.trim()) return;
    setLoading(true);
    setError('');
    setValidation(null);
    try {
      const result = await api.houseRules.validate(gameId, description);
      setValidation(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!description.trim()) return;
    setLoading(true);
    setError('');
    try {
      await api.houseRules.add(gameId, description);
      setDescription('');
      setValidation(null);
      onRuleAdded?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add rule');
    } finally {
      setLoading(false);
    }
  };

  const icon =
    validation?.recommendation === 'accept' ? (
      <CheckCircle className="text-green-400" size={24} />
    ) : validation?.recommendation === 'reject' ? (
      <XCircle className="text-red-400" size={24} />
    ) : validation ? (
      <AlertTriangle className="text-yellow-400" size={24} />
    ) : null;

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe your house rule... e.g. 'Players start with 10 extra coins'"
          className="input flex-1 min-h-[80px] resize-y"
        />
        <div className="flex flex-col gap-2">
          <VoiceInput onTranscript={(text) => setDescription((prev) => prev + ' ' + text)} />
        </div>
      </div>

      <div className="flex gap-2">
        <button onClick={handleValidate} disabled={loading || !description.trim()} className="btn-secondary">
          {loading ? <Loader size={16} className="animate-spin mr-2 inline" /> : null}
          Validate
        </button>
        <button
          onClick={handleAdd}
          disabled={loading || !description.trim()}
          className="btn-primary"
        >
          Add Rule
        </button>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {validation && (
        <div className="card space-y-3">
          <div className="flex items-center gap-3">
            {icon}
            <span className="font-medium capitalize">{validation.recommendation}</span>
          </div>

          <p className="text-sm text-gray-300">{validation.recommendation_reason}</p>

          {validation.contradiction && (
            <div className="bg-red-900/20 border border-red-800 rounded-lg p-3">
              <p className="text-sm text-red-300">
                <strong>Contradiction:</strong> {validation.contradiction_reason}
              </p>
            </div>
          )}

          <div className="grid grid-cols-3 gap-3 text-sm">
            <div>
              <span className="text-gray-500">Balance</span>
              <p className="text-gray-300 capitalize">{validation.balance_impact}</p>
            </div>
            <div>
              <span className="text-gray-500">Duration</span>
              <p className="text-gray-300 capitalize">{validation.length_impact}</p>
            </div>
            <div>
              <span className="text-gray-500">Complexity</span>
              <p className="text-gray-300 capitalize">{validation.complexity_impact}</p>
            </div>
          </div>

          {validation.logical_issues?.length > 0 && (
            <div>
              <p className="text-sm text-gray-500 mb-1">Logical Issues:</p>
              <ul className="text-sm text-yellow-300 space-y-1">
                {validation.logical_issues.map((issue, i) => (
                  <li key={i}>⚠️ {issue}</li>
                ))}
              </ul>
            </div>
          )}

          {validation.suggested_modification && (
            <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-3">
              <p className="text-sm text-blue-300">
                <strong>Suggestion:</strong> {validation.suggested_modification}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
