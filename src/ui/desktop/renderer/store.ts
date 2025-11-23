import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// Types for the store state
export interface TranscriptionSegment {
  id: string;
  text: string;
  timestamp: number;
  speaker?: string;
  confidence?: number;
}

export interface Insight {
  id: string;
  type: 'keyword' | 'entity' | 'sentiment' | 'topic';
  content: string;
  timestamp: number;
  metadata?: Record<string, any>;
}

export interface Summary {
  id: string;
  content: string;
  timestamp: number;
  keyPoints?: string[];
}

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error';

export interface Settings {
  websocketUrl: string;
  autoReconnect: boolean;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  audioInputDevice?: string;
  theme: 'dark' | 'light';
  notifications: boolean;
  autoScroll: boolean;
}

export interface AppState {
  // Transcription state
  transcription: TranscriptionSegment[];
  currentTranscription: string;

  // Insights state
  insights: Insight[];

  // Summary state
  summaries: Summary[];
  currentSummary: Summary | null;

  // Connection state
  connectionStatus: ConnectionStatus;
  connectionError: string | null;
  lastConnectedAt: number | null;
  reconnectAttempts: number;

  // Settings state (persisted)
  settings: Settings;

  // Actions for transcription
  addTranscriptionSegment: (segment: TranscriptionSegment) => void;
  updateCurrentTranscription: (text: string) => void;
  clearTranscription: () => void;

  // Actions for insights
  addInsight: (insight: Insight) => void;
  clearInsights: () => void;

  // Actions for summary
  addSummary: (summary: Summary) => void;
  setCurrentSummary: (summary: Summary | null) => void;
  clearSummaries: () => void;

  // Actions for connection
  setConnectionStatus: (status: ConnectionStatus) => void;
  setConnectionError: (error: string | null) => void;
  setLastConnectedAt: (timestamp: number | null) => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;

  // Actions for settings
  updateSettings: (settings: Partial<Settings>) => void;
  resetSettings: () => void;

  // Utility actions
  clearAll: () => void;
}

// Default settings
const defaultSettings: Settings = {
  websocketUrl: 'ws://localhost:8000/ws',
  autoReconnect: true,
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
  theme: 'dark',
  notifications: true,
  autoScroll: true,
};

// Initial state
const initialState = {
  transcription: [],
  currentTranscription: '',
  insights: [],
  summaries: [],
  currentSummary: null,
  connectionStatus: 'disconnected' as ConnectionStatus,
  connectionError: null,
  lastConnectedAt: null,
  reconnectAttempts: 0,
  settings: defaultSettings,
};

// Create the store with persistence for settings
export const useStore = create<AppState>()(
  persist(
    (set) => ({
      ...initialState,

      // Transcription actions
      addTranscriptionSegment: (segment) =>
        set((state) => ({
          transcription: [...state.transcription, segment],
          currentTranscription: '',
        })),

      updateCurrentTranscription: (text) =>
        set({ currentTranscription: text }),

      clearTranscription: () =>
        set({ transcription: [], currentTranscription: '' }),

      // Insights actions
      addInsight: (insight) =>
        set((state) => ({
          insights: [...state.insights, insight],
        })),

      clearInsights: () =>
        set({ insights: [] }),

      // Summary actions
      addSummary: (summary) =>
        set((state) => ({
          summaries: [...state.summaries, summary],
          currentSummary: summary,
        })),

      setCurrentSummary: (summary) =>
        set({ currentSummary: summary }),

      clearSummaries: () =>
        set({ summaries: [], currentSummary: null }),

      // Connection actions
      setConnectionStatus: (status) =>
        set({ connectionStatus: status }),

      setConnectionError: (error) =>
        set({ connectionError: error }),

      setLastConnectedAt: (timestamp) =>
        set({ lastConnectedAt: timestamp }),

      incrementReconnectAttempts: () =>
        set((state) => ({
          reconnectAttempts: state.reconnectAttempts + 1,
        })),

      resetReconnectAttempts: () =>
        set({ reconnectAttempts: 0 }),

      // Settings actions
      updateSettings: (newSettings) =>
        set((state) => ({
          settings: { ...state.settings, ...newSettings },
        })),

      resetSettings: () =>
        set({ settings: defaultSettings }),

      // Utility actions
      clearAll: () =>
        set({
          transcription: [],
          currentTranscription: '',
          insights: [],
          summaries: [],
          currentSummary: null,
          connectionError: null,
          reconnectAttempts: 0,
        }),
    }),
    {
      name: 'orchidea-rtstt-storage',
      storage: createJSONStorage(() => localStorage),
      // Only persist settings
      partialize: (state) => ({
        settings: state.settings,
      }),
    }
  )
);

// Selectors for optimized access
export const useTranscription = () => useStore((state) => state.transcription);
export const useCurrentTranscription = () => useStore((state) => state.currentTranscription);
export const useInsights = () => useStore((state) => state.insights);
export const useSummaries = () => useStore((state) => state.summaries);
export const useCurrentSummary = () => useStore((state) => state.currentSummary);
export const useConnectionStatus = () => useStore((state) => state.connectionStatus);
export const useConnectionError = () => useStore((state) => state.connectionError);
export const useSettings = () => useStore((state) => state.settings);
