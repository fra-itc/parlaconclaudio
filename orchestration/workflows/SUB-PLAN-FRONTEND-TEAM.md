# SUB-PLAN: FRONTEND TEAM
## Electron Desktop App + React Dashboard

---

**Worktree**: `../RTSTT-frontend`
**Branch**: `feature/ui-dashboard`
**Team**: 2 Sonnet Agents (Electron Architect, React Engineer)
**Duration**: 6 hours
**Priority**: ALTA (user interface)

---

## 🎯 OBIETTIVO

Sviluppare desktop app Electron per Windows 11 con React dashboard per visualizzazione real-time di transcription, keywords, speakers, e summary. WebSocket connection per low-latency updates.

---

## 📦 DELIVERABLES

1. **Electron Main Process** (`src/ui/desktop/main.js`)
2. **React App** (`src/ui/desktop/renderer/App.tsx`)
3. **WebSocket Hook** (`src/ui/desktop/renderer/hooks/useWebSocket.ts`)
4. **Transcription Panel** (`src/ui/desktop/renderer/components/TranscriptionPanel.tsx`)
5. **Insights Panel** (`src/ui/desktop/renderer/components/InsightsPanel.tsx`)
6. **Summary Panel** (`src/ui/desktop/renderer/components/SummaryPanel.tsx`)
7. **Settings Panel** (`src/ui/desktop/renderer/components/SettingsPanel.tsx`)
8. **Build Configuration** (`package.json`, `electron-builder.yml`)
9. **Tests** (Jest + React Testing Library)

---

## 📋 TASK BREAKDOWN

### TASK 1: Electron Setup (1h)

#### Step 1.1: Project Initialization (30min)
```bash
# In ../RTSTT-frontend/src/ui/desktop
npm init -y
npm install electron electron-builder
npm install react react-dom
npm install typescript @types/react @types/react-dom @types/node
npm install vite @vitejs/plugin-react
npm install zustand  # State management
npm install lucide-react  # Icons
```

```json
// package.json
{
  "name": "rtstt-desktop",
  "version": "1.0.0",
  "main": "main.js",
  "scripts": {
    "dev": "concurrently \"npm run dev:vite\" \"npm run dev:electron\"",
    "dev:vite": "vite",
    "dev:electron": "electron .",
    "build": "tsc && vite build",
    "build:win": "electron-builder --win --x64",
    "test": "jest"
  },
  "dependencies": {
    "electron": "^28.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "zustand": "^4.4.7"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "@types/react": "^18.2.45",
    "@types/react-dom": "^18.2.18",
    "@vitejs/plugin-react": "^4.2.1",
    "concurrently": "^8.2.2",
    "electron-builder": "^24.9.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.8"
  }
}
```

---

#### Step 1.2: Electron Main Process (30min)
```javascript
// File: src/ui/desktop/main.js

const { app, BrowserWindow, ipcMain, Tray, Menu } = require('electron');
const path = require('path');

let mainWindow;
let tray;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    icon: path.join(__dirname, 'assets/icon.ico'),
    title: 'Real-Time STT Orchestrator'
  });

  // Load app
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, 'dist/index.html'));
  }

  // System tray
  createTray();

  // Window events
  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

function createTray() {
  tray = new Tray(path.join(__dirname, 'assets/icon-tray.ico'));

  const contextMenu = Menu.buildFromTemplate([
    { label: 'Show App', click: () => mainWindow.show() },
    { label: 'Start Recording', click: () => mainWindow.webContents.send('start-recording') },
    { label: 'Stop Recording', click: () => mainWindow.webContents.send('stop-recording') },
    { type: 'separator' },
    { label: 'Quit', click: () => { app.isQuitting = true; app.quit(); }}
  ]);

  tray.setToolTip('RTSTT - Idle');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    mainWindow.show();
  });
}

// IPC Handlers
ipcMain.handle('get-audio-devices', async () => {
  // Call native module or backend API
  return [
    { id: 'default', name: 'System Audio (Loopback)', type: 'loopback' },
    { id: 'mic-1', name: 'Microphone Array', type: 'input' }
  ];
});

ipcMain.handle('start-session', async (event, config) => {
  console.log('Starting session with config:', config);
  // Connect to backend WebSocket
  return { sessionId: 'session-' + Date.now() };
});

ipcMain.handle('stop-session', async (event, sessionId) => {
  console.log('Stopping session:', sessionId);
  return { success: true };
});

// App lifecycle
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
```

```javascript
// File: src/ui/desktop/preload.js

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getAudioDevices: () => ipcRenderer.invoke('get-audio-devices'),
  startSession: (config) => ipcRenderer.invoke('start-session', config),
  stopSession: (sessionId) => ipcRenderer.invoke('stop-session', sessionId),
  onStartRecording: (callback) => ipcRenderer.on('start-recording', callback),
  onStopRecording: (callback) => ipcRenderer.on('stop-recording', callback)
});
```

---

### TASK 2: React App Setup (1h)

#### Step 2.1: App Structure (30min)
```typescript
// File: src/ui/desktop/renderer/App.tsx

import React, { useState, useEffect } from 'react';
import { TranscriptionPanel } from './components/TranscriptionPanel';
import { InsightsPanel } from './components/InsightsPanel';
import { SummaryPanel } from './components/SummaryPanel';
import { SettingsPanel } from './components/SettingsPanel';
import { useWebSocket } from './hooks/useWebSocket';
import { useStore } from './store';
import './App.css';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('transcription');
  const { status, connect, disconnect, sendMessage } = useWebSocket('ws://localhost:8000/ws');
  const { session, transcription, insights, summary } = useStore();

  const handleStartRecording = async () => {
    // Get audio device
    const devices = await window.electronAPI.getAudioDevices();
    const defaultDevice = devices.find(d => d.type === 'loopback');

    // Start session via WebSocket
    connect();
    sendMessage({
      type: 'transcription_start',
      timestamp: Date.now(),
      payload: {
        device_id: defaultDevice?.id || 'default',
        language: 'en',
        enable_nlp: true,
        enable_summary: true
      }
    });
  };

  const handleStopRecording = () => {
    sendMessage({
      type: 'transcription_stop',
      timestamp: Date.now(),
      payload: { save_session: true }
    });
    disconnect();
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Real-Time STT Orchestrator</h1>
        <div className="controls">
          <button
            onClick={handleStartRecording}
            disabled={status === 'connected'}
            className="btn btn-primary"
          >
            🎙️ Start Recording
          </button>
          <button
            onClick={handleStopRecording}
            disabled={status !== 'connected'}
            className="btn btn-danger"
          >
            ⏹️ Stop Recording
          </button>
          <span className={`status status-${status}`}>
            {status === 'connected' ? '🟢 Recording' : '🔴 Idle'}
          </span>
        </div>
      </header>

      <nav className="app-nav">
        <button
          className={activeTab === 'transcription' ? 'active' : ''}
          onClick={() => setActiveTab('transcription')}
        >
          📝 Transcription
        </button>
        <button
          className={activeTab === 'insights' ? 'active' : ''}
          onClick={() => setActiveTab('insights')}
        >
          🔍 Insights
        </button>
        <button
          className={activeTab === 'summary' ? 'active' : ''}
          onClick={() => setActiveTab('summary')}
        >
          📊 Summary
        </button>
        <button
          className={activeTab === 'settings' ? 'active' : ''}
          onClick={() => setActiveTab('settings')}
        >
          ⚙️ Settings
        </button>
      </nav>

      <main className="app-main">
        {activeTab === 'transcription' && <TranscriptionPanel />}
        {activeTab === 'insights' && <InsightsPanel />}
        {activeTab === 'summary' && <SummaryPanel />}
        {activeTab === 'settings' && <SettingsPanel />}
      </main>

      <footer className="app-footer">
        <span>Session: {session?.id || 'None'}</span>
        <span>Words: {transcription?.wordCount || 0}</span>
        <span>Duration: {session?.duration || '00:00'}</span>
      </footer>
    </div>
  );
};

export default App;
```

---

#### Step 2.2: WebSocket Hook (30min)
```typescript
// File: src/ui/desktop/renderer/hooks/useWebSocket.ts

import { useState, useEffect, useCallback, useRef } from 'react';
import { useStore } from '../store';

type WebSocketStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export const useWebSocket = (url: string) => {
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number>();
  const { addTranscription, updateInsights, updateSummary, setError } = useStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    setStatus('connecting');
    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setStatus('connected');
      // Start ping interval
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
        }
      }, 30000);
      (ws as any).pingInterval = pingInterval;
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleMessage(message);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStatus('error');
      setError('WebSocket connection error');
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
      setStatus('disconnected');
      clearInterval((ws as any).pingInterval);

      // Auto-reconnect after 3 seconds
      reconnectTimeoutRef.current = window.setTimeout(() => {
        console.log('Attempting to reconnect...');
        connect();
      }, 3000);
    };

    wsRef.current = ws;
  }, [url]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus('disconnected');
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, []);

  const handleMessage = (message: any) => {
    switch (message.type) {
      case 'transcription_update':
        addTranscription(message.payload);
        break;
      case 'nlp_insights':
        updateInsights(message.payload);
        break;
      case 'summary_update':
        updateSummary(message.payload);
        break;
      case 'status_update':
        console.log('Status:', message.payload.status);
        break;
      case 'error':
        setError(message.payload.message);
        break;
      case 'pong':
        // Pong received, connection alive
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  };

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return { status, connect, disconnect, sendMessage };
};
```

---

### TASK 3: React Components (2h)

```typescript
// File: src/ui/desktop/renderer/components/TranscriptionPanel.tsx

import React, { useRef, useEffect } from 'react';
import { useStore } from '../store';
import './TranscriptionPanel.css';

export const TranscriptionPanel: React.FC = () => {
  const { transcription } = useStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcription.segments]);

  return (
    <div className="transcription-panel">
      <div className="transcription-header">
        <h2>Live Transcription</h2>
        <div className="transcription-controls">
          <button className="btn-icon" title="Clear">🗑️</button>
          <button className="btn-icon" title="Export">💾</button>
          <button className="btn-icon" title="Copy">📋</button>
        </div>
      </div>

      <div className="transcription-content" ref={scrollRef}>
        {transcription.segments.length === 0 ? (
          <div className="empty-state">
            <p>No transcription yet. Click "Start Recording" to begin.</p>
          </div>
        ) : (
          transcription.segments.map((segment, index) => (
            <div
              key={index}
              className={`transcription-segment ${segment.is_partial ? 'partial' : 'final'}`}
            >
              <span className="timestamp">
                {formatTimestamp(segment.timestamp_start_ms)}
              </span>
              <span className="text">{segment.text}</span>
              <span className="confidence">
                {(segment.confidence * 100).toFixed(0)}%
              </span>
            </div>
          ))
        )}

        {transcription.partialText && (
          <div className="transcription-segment partial live">
            <span className="timestamp">Live</span>
            <span className="text">{transcription.partialText}</span>
            <span className="spinner">⏳</span>
          </div>
        )}
      </div>

      <div className="transcription-footer">
        <span>Total Words: {transcription.wordCount}</span>
        <span>Duration: {formatDuration(transcription.duration_ms)}</span>
        <span>Avg Confidence: {(transcription.avgConfidence * 100).toFixed(1)}%</span>
      </div>
    </div>
  );
};

function formatTimestamp(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function formatDuration(ms: number): string {
  return formatTimestamp(ms);
}
```

```typescript
// File: src/ui/desktop/renderer/components/InsightsPanel.tsx

import React from 'react';
import { useStore } from '../store';
import './InsightsPanel.css';

export const InsightsPanel: React.FC = () => {
  const { insights } = useStore();

  return (
    <div className="insights-panel">
      <section className="keywords-section">
        <h2>🏷️ Keywords</h2>
        <div className="keywords-cloud">
          {insights.keywords.map((kw, index) => (
            <span
              key={index}
              className="keyword-tag"
              style={{ fontSize: `${0.8 + kw.relevance_score * 0.6}rem` }}
            >
              {kw.keyword}
            </span>
          ))}
        </div>
      </section>

      <section className="speakers-section">
        <h2>👥 Speakers</h2>
        <div className="speakers-timeline">
          {insights.speakers.map((speaker, index) => (
            <div key={index} className="speaker-segment">
              <span className="speaker-id">{speaker.speaker_id}</span>
              <span className="speaker-time">
                {formatTimestamp(speaker.start_ms)} - {formatTimestamp(speaker.end_ms)}
              </span>
              <div className="speaker-bar" style={{
                width: `${((speaker.end_ms - speaker.start_ms) / insights.totalDuration) * 100}%`
              }}></div>
            </div>
          ))}
        </div>
      </section>

      {insights.sentiment && (
        <section className="sentiment-section">
          <h2>😊 Sentiment</h2>
          <div className={`sentiment-indicator sentiment-${insights.sentiment.label}`}>
            <span className="sentiment-emoji">
              {getSentimentEmoji(insights.sentiment.label)}
            </span>
            <span className="sentiment-label">{insights.sentiment.label}</span>
            <span className="sentiment-score">
              {(insights.sentiment.score * 100).toFixed(0)}%
            </span>
          </div>
        </section>
      )}
    </div>
  );
};

function getSentimentEmoji(label: string): string {
  switch (label) {
    case 'positive': return '😊';
    case 'neutral': return '😐';
    case 'negative': return '😞';
    default: return '😐';
  }
}
```

---

### TASK 4: State Management (30min)

```typescript
// File: src/ui/desktop/renderer/store.ts

import { create } from 'zustand';

interface TranscriptionSegment {
  text: string;
  confidence: number;
  timestamp_start_ms: number;
  timestamp_end_ms: number;
  is_partial: boolean;
  words: any[];
}

interface AppState {
  session: { id: string; duration: string } | null;
  transcription: {
    segments: TranscriptionSegment[];
    partialText: string;
    wordCount: number;
    duration_ms: number;
    avgConfidence: number;
  };
  insights: {
    keywords: Array<{ keyword: string; relevance_score: number }>;
    speakers: Array<{ speaker_id: string; start_ms: number; end_ms: number }>;
    sentiment: { label: string; score: number } | null;
    totalDuration: number;
  };
  summary: {
    text: string;
    keyPoints: string[];
    compressionRatio: number;
    isFinal: boolean;
  };
  error: string | null;

  // Actions
  addTranscription: (payload: any) => void;
  updateInsights: (payload: any) => void;
  updateSummary: (payload: any) => void;
  setError: (error: string) => void;
  clearSession: () => void;
}

export const useStore = create<AppState>((set) => ({
  session: null,
  transcription: {
    segments: [],
    partialText: '',
    wordCount: 0,
    duration_ms: 0,
    avgConfidence: 0
  },
  insights: {
    keywords: [],
    speakers: [],
    sentiment: null,
    totalDuration: 0
  },
  summary: {
    text: '',
    keyPoints: [],
    compressionRatio: 0,
    isFinal: false
  },
  error: null,

  addTranscription: (payload) => set((state) => {
    const newSegment = {
      text: payload.text,
      confidence: payload.confidence,
      timestamp_start_ms: payload.timestamp_start_ms,
      timestamp_end_ms: payload.timestamp_end_ms,
      is_partial: payload.is_partial,
      words: payload.words || []
    };

    if (payload.is_partial) {
      return {
        transcription: {
          ...state.transcription,
          partialText: payload.text
        }
      };
    } else {
      const segments = [...state.transcription.segments, newSegment];
      return {
        transcription: {
          segments,
          partialText: '',
          wordCount: segments.reduce((sum, seg) => sum + seg.text.split(' ').length, 0),
          duration_ms: payload.timestamp_end_ms,
          avgConfidence: segments.reduce((sum, seg) => sum + seg.confidence, 0) / segments.length
        }
      };
    }
  }),

  updateInsights: (payload) => set((state) => ({
    insights: {
      keywords: payload.keywords || state.insights.keywords,
      speakers: payload.speakers || state.insights.speakers,
      sentiment: payload.sentiment || state.insights.sentiment,
      totalDuration: payload.duration_ms || state.insights.totalDuration
    }
  })),

  updateSummary: (payload) => set(() => ({
    summary: {
      text: payload.summary,
      keyPoints: payload.key_points || [],
      compressionRatio: payload.compression_ratio || 0,
      isFinal: payload.is_final
    }
  })),

  setError: (error) => set({ error }),

  clearSession: () => set({
    session: null,
    transcription: {
      segments: [],
      partialText: '',
      wordCount: 0,
      duration_ms: 0,
      avgConfidence: 0
    },
    insights: {
      keywords: [],
      speakers: [],
      sentiment: null,
      totalDuration: 0
    },
    summary: {
      text: '',
      keyPoints: [],
      compressionRatio: 0,
      isFinal: false
    },
    error: null
  })
}));
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Electron app si avvia su Windows 11
- [ ] System tray integration funzionante
- [ ] WebSocket connection stabile
- [ ] Real-time transcription display (<100ms latency)
- [ ] Keywords e speakers visualizzati correttamente
- [ ] Summary panel aggiornato
- [ ] Export transcription (TXT, JSON, SRT)
- [ ] Settings panel per configurazione
- [ ] Build .exe installer funzionante

---

## 🚀 COMANDI ESECUZIONE

```bash
cd ../RTSTT-frontend/src/ui/desktop

# Install dependencies
npm install

# Development mode
npm run dev

# Build Windows installer
npm run build:win

# Test
npm test
```

---

**BUON LAVORO, FRONTEND TEAM! 🎨**
