// ---------- Game Types ----------

export interface GameComponent {
  name: string;
  quantity: number | null;
  description: string;
}

export interface TurnPhase {
  name: string;
  description: string;
  actions: string[];
}

export interface VictoryCondition {
  description: string;
  type: string;
}

export interface GameSchema {
  name: string;
  min_players: number;
  max_players: number;
  estimated_duration_minutes: number | null;
  components: GameComponent[];
  setup_instructions: string[];
  turn_structure: TurnPhase[];
  victory_conditions: VictoryCondition[];
  special_rules: string[];
  edge_cases: string[];
  summary: string;
}

export interface HouseRule {
  id: string;
  description: string;
  modifies_rule: string | null;
  impact: string | null;
  validated: boolean;
  contradiction: boolean;
  contradiction_reason: string | null;
}

export interface Game {
  id: string;
  name: string;
  slug: string;
  source: string;
  structured_rules: GameSchema | null;
  house_rules: HouseRule[];
  created_at: string;
}

// ---------- Session Types ----------

export interface GameSession {
  id: string;
  game_id: string;
  players: string[];
  current_turn: number;
  turn_order: string[];
  game_state: Record<string, unknown>;
  status: 'setup' | 'active' | 'paused' | 'ended';
}

// ---------- Explanation Types ----------

export type ExplanationMode = 'quick_start' | 'step_by_step' | 'playthrough' | 'qa';

export interface ExplanationResponse {
  game_id: string;
  mode: string;
  explanation: string;
}

export interface QAResponse {
  game_id: string;
  question: string;
  answer: string;
  citations: string[];
  confidence: 'high' | 'medium' | 'low';
  conflicts: string[];
}

// ---------- House Rule Validation ----------

export interface HouseRuleValidation {
  game_id: string;
  house_rule: string;
  contradiction: boolean;
  contradiction_reason: string | null;
  impacted_rules: string[];
  balance_impact: string;
  length_impact: string;
  complexity_impact: string;
  logical_issues: string[];
  recommendation: 'accept' | 'modify' | 'reject';
  recommendation_reason: string;
  suggested_modification: string | null;
}

// ---------- Moderation Types ----------

export interface MoveValidation {
  session_id: string;
  player: string;
  action: string;
  valid: boolean;
  reason: string;
  rule_reference: string;
  suggestion: string | null;
}

export interface DisputeResolution {
  game_id: string;
  session_id: string;
  dispute: string;
  resolution: string;
  citations: string[];
  interpretation_level: string;
  confidence: string;
  flagged: boolean;
}

// ---------- WebSocket Types ----------

export interface WSMessage {
  type: 'chat' | 'turn_action' | 'system' | 'voice_ack' | 'turn_update' | 'dispute_result';
  player?: string;
  content?: string;
  action?: string;
  [key: string]: unknown;
}

// ---------- Auth ----------

export interface User {
  id: string;
  username: string;
  avatar_url: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
