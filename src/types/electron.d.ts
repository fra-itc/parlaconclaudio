/**
 * TypeScript definitions for Electron IPC API
 * This file provides type safety for window.electronAPI exposed via contextBridge
 */

export interface RecordingAPI {
  start: () => Promise<{ success: boolean; message: string }>;
  stop: () => Promise<{ success: boolean; message: string }>;
}

export interface AudioDevice {
  id: string;
  name: string;
  isDefault: boolean;
}

export interface AudioSettings {
  deviceId?: string;
  sampleRate?: number;
  channels?: number;
  bitDepth?: number;
}

export interface AudioAPI {
  getDevices: () => Promise<{ success: boolean; devices: AudioDevice[] }>;
  updateSettings: (settings: AudioSettings) => Promise<{ success: boolean }>;
}

export interface TranscriptionResult {
  success: boolean;
  text: string;
  confidence: number;
}

export interface TranscriptionAPI {
  process: (audioData: ArrayBuffer | Blob) => Promise<TranscriptionResult>;
  onUpdate: (callback: (data: TranscriptionResult) => void) => () => void;
}

export interface WindowAPI {
  minimize: () => Promise<void>;
  maximize: () => Promise<void>;
  close: () => Promise<void>;
  hide: () => Promise<void>;
  show: () => Promise<void>;
  onStateChange: (callback: (state: string) => void) => () => void;
}

export interface AppAPI {
  getVersion: () => Promise<string>;
  getPath: (name: string) => Promise<string>;
  on: (channel: string, callback: (...args: any[]) => void) => () => void;
}

export interface Settings {
  [key: string]: any;
}

export interface SettingsAPI {
  get: () => Promise<Settings>;
  update: (settings: Settings) => Promise<{ success: boolean }>;
  reset: () => Promise<{ success: boolean }>;
  onChange: (callback: (settings: Settings) => void) => () => void;
}

export interface ElectronAPI {
  recording: RecordingAPI;
  audio: AudioAPI;
  transcription: TranscriptionAPI;
  window: WindowAPI;
  app: AppAPI;
  settings: SettingsAPI;
  isDev: () => boolean;
  platform: string;
  send: (channel: string, data: any) => void;
  invoke: (channel: string, ...args: any[]) => Promise<any>;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
    __electronAPIVersion: string;
  }
}

export {};
