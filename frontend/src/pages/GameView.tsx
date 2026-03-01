import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Users, Clock, BookOpen, Play, MessageCircle, Gavel,
  ChevronDown, ChevronUp, Loader, PlusCircle
} from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/gameStore';
import { HouseRuleForm } from '../components/HouseRuleForm';
import type { Game, HouseRule } from '../types';

export function GameViewPage() {
  const { id } = useParams<{ id: string }>();
  const { currentGame, setCurrentGame } = useAppStore();
  const [loading, setLoading] = useState(true);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));
  const [showHouseRuleForm, setShowHouseRuleForm] = useState(false);
  const [houseRules, setHouseRules] = useState<HouseRule[]>([]);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api.games
      .get(id)
      .then((game) => {
        setCurrentGame(game);
        setHouseRules(game.house_rules || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id, setCurrentGame]);

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      next.has(section) ? next.delete(section) : next.add(section);
      return next;
    });
  };

  const refreshHouseRules = async () => {
    if (!id) return;
    const result = await api.houseRules.list(id);
    setHouseRules(result.house_rules);
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

  const rules = currentGame.structured_rules;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card bg-gradient-to-r from-game-card to-brand-900/20">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="font-display text-3xl font-bold text-white">{currentGame.name}</h1>
            {rules && (
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
                <span className="flex items-center gap-1">
                  <Users size={14} /> {rules.min_players}–{rules.max_players} players
                </span>
                {rules.estimated_duration_minutes && (
                  <span className="flex items-center gap-1">
                    <Clock size={14} /> {rules.estimated_duration_minutes} min
                  </span>
                )}
                <span className={`badge ${currentGame.source === 'ocr' ? 'badge-info' : 'badge-success'}`}>
                  {currentGame.source === 'ocr' ? 'OCR' : 'Search'}
                </span>
              </div>
            )}
            {rules?.summary && <p className="mt-3 text-gray-300">{rules.summary}</p>}
          </div>
          <div className="flex gap-2">
            <Link to={`/explain/${currentGame.id}`} className="btn-primary flex items-center gap-2">
              <BookOpen size={16} /> Explain
            </Link>
            <Link to={`/moderate/${currentGame.id}`} className="btn-secondary flex items-center gap-2">
              <Play size={16} /> Moderate
            </Link>
          </div>
        </div>
      </div>

      {rules && (
        <>
          {/* Components */}
          <CollapsibleSection
            title="Components"
            section="components"
            expanded={expandedSections.has('components')}
            onToggle={() => toggleSection('components')}
          >
            {rules.components.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {rules.components.map((comp, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-game-bg rounded-lg">
                    <div className="text-brand-400 font-mono text-sm">
                      {comp.quantity ? `×${comp.quantity}` : '—'}
                    </div>
                    <div>
                      <p className="text-white font-medium">{comp.name}</p>
                      {comp.description && <p className="text-gray-500 text-xs">{comp.description}</p>}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No components listed.</p>
            )}
          </CollapsibleSection>

          {/* Setup */}
          <CollapsibleSection
            title="Setup Instructions"
            section="setup"
            expanded={expandedSections.has('setup')}
            onToggle={() => toggleSection('setup')}
          >
            <ol className="space-y-2">
              {rules.setup_instructions.map((step, i) => (
                <li key={i} className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-brand-600 text-white text-xs flex items-center justify-center">
                    {i + 1}
                  </span>
                  <span className="text-gray-300">{step}</span>
                </li>
              ))}
            </ol>
          </CollapsibleSection>

          {/* Turn Structure */}
          <CollapsibleSection
            title="Turn Structure"
            section="turns"
            expanded={expandedSections.has('turns')}
            onToggle={() => toggleSection('turns')}
          >
            <div className="space-y-4">
              {rules.turn_structure.map((phase, i) => (
                <div key={i} className="border-l-2 border-brand-500 pl-4">
                  <h4 className="text-white font-medium">{phase.name}</h4>
                  <p className="text-gray-400 text-sm mt-1">{phase.description}</p>
                  {phase.actions.length > 0 && (
                    <ul className="mt-2 space-y-1">
                      {phase.actions.map((action, j) => (
                        <li key={j} className="text-gray-500 text-sm flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-brand-400" />
                          {action}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </CollapsibleSection>

          {/* Victory Conditions */}
          <CollapsibleSection
            title="Victory Conditions"
            section="victory"
            expanded={expandedSections.has('victory')}
            onToggle={() => toggleSection('victory')}
          >
            <div className="space-y-2">
              {rules.victory_conditions.map((vc, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-game-bg rounded-lg">
                  <span className="badge-success">{vc.type}</span>
                  <span className="text-gray-300">{vc.description}</span>
                </div>
              ))}
            </div>
          </CollapsibleSection>

          {/* Special Rules */}
          {rules.special_rules.length > 0 && (
            <CollapsibleSection
              title="Special Rules"
              section="special"
              expanded={expandedSections.has('special')}
              onToggle={() => toggleSection('special')}
            >
              <ul className="space-y-2">
                {rules.special_rules.map((rule, i) => (
                  <li key={i} className="text-gray-300 flex items-start gap-2">
                    <span className="text-brand-400 mt-1">•</span>
                    {rule}
                  </li>
                ))}
              </ul>
            </CollapsibleSection>
          )}
        </>
      )}

      {/* House Rules */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-lg font-semibold text-white flex items-center gap-2">
            <Gavel size={20} className="text-brand-400" />
            House Rules
          </h3>
          <button
            onClick={() => setShowHouseRuleForm(!showHouseRuleForm)}
            className="btn-secondary text-sm py-1.5 flex items-center gap-1"
          >
            <PlusCircle size={14} />
            Add Rule
          </button>
        </div>

        {houseRules.length > 0 ? (
          <div className="space-y-3 mb-4">
            {houseRules.map((rule) => (
              <div
                key={rule.id}
                className={`p-3 rounded-lg border ${
                  rule.contradiction
                    ? 'border-red-800 bg-red-900/10'
                    : 'border-game-border bg-game-bg'
                }`}
              >
                <p className="text-gray-300">{rule.description}</p>
                {rule.contradiction && (
                  <p className="text-xs text-red-400 mt-1">⚠ {rule.contradiction_reason}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm mb-4">No house rules added yet.</p>
        )}

        {showHouseRuleForm && currentGame && (
          <HouseRuleForm gameId={currentGame.id} onRuleAdded={refreshHouseRules} />
        )}
      </div>
    </div>
  );
}

// ---------- Collapsible Section ----------

function CollapsibleSection({
  title,
  section,
  expanded,
  onToggle,
  children,
}: {
  title: string;
  section: string;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="card">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between text-left"
      >
        <h3 className="font-display text-lg font-semibold text-white">{title}</h3>
        {expanded ? (
          <ChevronUp size={20} className="text-gray-400" />
        ) : (
          <ChevronDown size={20} className="text-gray-400" />
        )}
      </button>
      {expanded && <div className="mt-4">{children}</div>}
    </div>
  );
}
