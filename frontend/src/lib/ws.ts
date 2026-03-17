// WebSocket client with auto-reconnect and exponential backoff

import type { WSEvent } from './types';

type WSCallback = (event: WSEvent) => void;

const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;
const MAX_RECONNECT_DELAY = 30000;
const INITIAL_RECONNECT_DELAY = 1000;

export class SprintWebSocket {
  private ws: WebSocket | null = null;
  private reconnectDelay = INITIAL_RECONNECT_DELAY;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private listeners = new Set<WSCallback>();
  private lastSequence = 0;
  private _isConnected = false;
  private _sprintId: string;
  private intentionallyClosed = false;

  constructor(sprintId: string) {
    this._sprintId = sprintId;
  }

  get isConnected() { return this._isConnected; }
  get sprintId() { return this._sprintId; }

  connect() {
    this.intentionallyClosed = false;
    const url = `${WS_BASE}/ws/sprints/${this._sprintId}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this._isConnected = true;
      this.reconnectDelay = INITIAL_RECONNECT_DELAY;
      // Request catch-up if we have a last sequence
      if (this.lastSequence > 0) {
        this.ws?.send(JSON.stringify({ type: 'catch-up', lastSequence: this.lastSequence }));
      }
    };

    this.ws.onmessage = (ev) => {
      try {
        const event: WSEvent = JSON.parse(ev.data);
        if (event.sequence) this.lastSequence = event.sequence;
        this.listeners.forEach(cb => cb(event));
      } catch {
        // ignore non-JSON messages (like "pong")
      }
    };

    this.ws.onclose = () => {
      this._isConnected = false;
      if (!this.intentionallyClosed) this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, MAX_RECONNECT_DELAY);
      this.connect();
    }, this.reconnectDelay);
  }

  subscribe(callback: WSCallback) {
    this.listeners.add(callback);
    return () => { this.listeners.delete(callback); };
  }

  disconnect() {
    this.intentionallyClosed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
    this._isConnected = false;
  }
}
