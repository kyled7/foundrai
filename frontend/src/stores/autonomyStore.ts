import { create } from 'zustand';
import type { AutonomyMatrix, AutonomyProfile, TrustScore, ActionType, AutonomyMode } from '../lib/types';

interface AutonomyStore {
  autonomyMatrix: AutonomyMatrix | null;
  trustScores: TrustScore[];
  profiles: AutonomyProfile[];
  activeProfile: string | null;
  loading: boolean;
  error: string | null;

  setMatrix: (matrix: AutonomyMatrix) => void;
  setTrustScores: (scores: TrustScore[]) => void;
  setProfiles: (profiles: AutonomyProfile[]) => void;
  setActiveProfile: (profileId: string | null) => void;

  loadConfig: (projectId: string) => Promise<void>;
  saveConfig: (projectId: string, matrix: Record<string, Record<ActionType, AutonomyMode>>) => Promise<void>;
  applyProfile: (projectId: string, profileId: string) => Promise<void>;
  loadTrustScores: (projectId: string) => Promise<void>;
  loadProfiles: () => Promise<void>;

  updateCell: (agentRole: string, actionType: ActionType, mode: AutonomyMode) => void;
  clearError: () => void;
}

/**
 * Fetch autonomy configuration for a project
 */
async function fetchConfig(projectId: string): Promise<AutonomyMatrix> {
  const res = await fetch(`/api/projects/${projectId}/autonomy/config`);
  if (!res.ok) {
    throw new Error(`Failed to fetch autonomy config: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Update autonomy configuration for a project
 */
async function updateConfig(
  projectId: string,
  matrix: Record<string, Record<ActionType, AutonomyMode>>
): Promise<AutonomyMatrix> {
  const res = await fetch(`/api/projects/${projectId}/autonomy/config`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ matrix }),
  });
  if (!res.ok) {
    throw new Error(`Failed to update autonomy config: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Fetch available autonomy profiles
 */
async function fetchProfiles(): Promise<AutonomyProfile[]> {
  const res = await fetch('/api/autonomy/profiles');
  if (!res.ok) {
    throw new Error(`Failed to fetch autonomy profiles: ${res.statusText}`);
  }
  const data = await res.json();
  return data.profiles || [];
}

/**
 * Apply a profile to a project
 */
async function applyProfileToProject(projectId: string, profileId: string): Promise<void> {
  const res = await fetch(`/api/projects/${projectId}/autonomy/apply-profile/${profileId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to apply profile: ${res.statusText}`);
  }
}

/**
 * Fetch trust scores for a project
 */
async function fetchTrustScores(projectId: string): Promise<TrustScore[]> {
  const res = await fetch(`/api/projects/${projectId}/autonomy/trust-scores`);
  if (!res.ok) {
    throw new Error(`Failed to fetch trust scores: ${res.statusText}`);
  }
  const data = await res.json();
  return data.trust_scores || [];
}

export const useAutonomyStore = create<AutonomyStore>((set, get) => ({
  autonomyMatrix: null,
  trustScores: [],
  profiles: [],
  activeProfile: null,
  loading: false,
  error: null,

  setMatrix: (matrix) =>
    set({ autonomyMatrix: matrix }),

  setTrustScores: (scores) =>
    set({ trustScores: scores }),

  setProfiles: (profiles) =>
    set({ profiles }),

  setActiveProfile: (profileId) =>
    set({ activeProfile: profileId }),

  loadConfig: async (projectId) => {
    set({ loading: true, error: null });
    try {
      const matrix = await fetchConfig(projectId);
      set({ autonomyMatrix: matrix, loading: false });
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Failed to load autonomy config';
      set({ error, loading: false });
      console.error('Failed to load autonomy config:', err);
    }
  },

  saveConfig: async (projectId, matrix) => {
    set({ loading: true, error: null });
    try {
      const updated = await updateConfig(projectId, matrix);
      set({ autonomyMatrix: updated, loading: false });
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Failed to save autonomy config';
      set({ error, loading: false });
      console.error('Failed to save autonomy config:', err);
      throw err; // Re-throw so UI can handle it
    }
  },

  applyProfile: async (projectId, profileId) => {
    set({ loading: true, error: null });
    try {
      await applyProfileToProject(projectId, profileId);
      // Reload the config after applying profile
      const matrix = await fetchConfig(projectId);
      set({ autonomyMatrix: matrix, activeProfile: profileId, loading: false });
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Failed to apply profile';
      set({ error, loading: false });
      console.error('Failed to apply profile:', err);
      throw err;
    }
  },

  loadTrustScores: async (projectId) => {
    set({ loading: true, error: null });
    try {
      const scores = await fetchTrustScores(projectId);
      set({ trustScores: scores, loading: false });
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Failed to load trust scores';
      set({ error, loading: false });
      console.error('Failed to load trust scores:', err);
    }
  },

  loadProfiles: async () => {
    set({ loading: true, error: null });
    try {
      const profiles = await fetchProfiles();
      set({ profiles, loading: false });
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Failed to load profiles';
      set({ error, loading: false });
      console.error('Failed to load profiles:', err);
    }
  },

  updateCell: (agentRole, actionType, mode) => {
    const { autonomyMatrix } = get();
    if (!autonomyMatrix) return;

    const updatedMatrix = { ...autonomyMatrix.matrix };
    if (!updatedMatrix[agentRole]) {
      updatedMatrix[agentRole] = {} as Record<ActionType, AutonomyMode>;
    }
    updatedMatrix[agentRole] = {
      ...updatedMatrix[agentRole],
      [actionType]: mode,
    };

    set({
      autonomyMatrix: {
        ...autonomyMatrix,
        matrix: updatedMatrix,
        updated_at: new Date().toISOString(),
      },
    });
  },

  clearError: () => set({ error: null }),
}));
