/** API client for settings endpoints. */

import { api } from './client';

export interface KeyStatus {
  provider: string;
  env_var: string;
  configured: boolean;
}

export interface KeysResponse {
  keys: KeyStatus[];
}

export interface ValidateResponse {
  provider: string;
  valid: boolean;
  error: string | null;
}

export function listKeys(): Promise<KeysResponse> {
  return api.get<KeysResponse>('/settings/keys');
}

export function setKey(provider: string, apiKey: string): Promise<KeyStatus> {
  return api.post<KeyStatus>('/settings/keys', { provider, api_key: apiKey });
}

export async function deleteKey(provider: string): Promise<KeyStatus> {
  const resp = await fetch(`/api/settings/keys/${provider}`, { method: 'DELETE' });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(body.detail ?? resp.statusText);
  }
  return resp.json();
}

export function validateKeys(): Promise<ValidateResponse[]> {
  return api.get<ValidateResponse[]>('/settings/keys/validate');
}
