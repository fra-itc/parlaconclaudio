# ISTRUZIONI PER CLAUDE CODE CLI - FRONTEND TEAM
## Electron Desktop App + React Dashboard

**IMPORTANTE**: Agente autonomo nel worktree `RTSTT-frontend` (branch: `feature/ui-dashboard`). Parallelizza con **5 sub-agenti, 2 ondate**.

---

## 🎯 OBIETTIVO
Desktop app Electron per Windows 11 con React dashboard real-time (transcription + insights + summary)

## 📊 TARGET
- **Durata**: 4-6 ore
- **Parallelismo**: 2 ondate, 5 sub-agenti
- **Tech**: Electron 28 + React 18 + TypeScript + Zustand + WebSocket

---

## 🔀 STRATEGIA PARALLELIZZAZIONE

```
ONDATA 1: Foundation (3 paralleli)
├── Sub-Agent 1: Electron Setup + Main Process
├── Sub-Agent 2: React App + Components Base
└── Sub-Agent 3: WebSocket Hook + State Management
      ↓
ONDATA 2: Features (2 paralleli)
├── Sub-Agent 4: Transcription + Insights Panels
└── Sub-Agent 5: Summary + Settings Panels
```

### CONFLICT AVOIDANCE
- Sub-Agent 1 → `main.js`, `preload.js`, `package.json`
- Sub-Agent 2 → `src/ui/desktop/renderer/App.tsx`, `components/`
- Sub-Agent 3 → `hooks/useWebSocket.ts`, `store.ts`
- Sub-Agent 4 → `components/TranscriptionPanel.tsx`, `InsightsPanel.tsx`
- Sub-Agent 5 → `components/SummaryPanel.tsx`, `SettingsPanel.tsx`

---

## 🚀 ONDATA 1: FOUNDATION

### Sub-Agent 1: Electron Setup
**Task tool**:
```
Setup Electron project con system tray e IPC:

FILES:
- src/ui/desktop/main.js (main process)
- src/ui/desktop/preload.js (context bridge)
- package.json (dependencies)

COMANDI:
cd src/ui/desktop
npm init -y
npm install electron electron-builder react react-dom typescript vite

DELIVERABLE: Electron app avviabile
COMMIT: "[FRONTEND-SUB-1] Setup Electron"
```

### Sub-Agent 2: React Base
**Task tool**:
```
Setup React app base con routing:

FILES:
- src/ui/desktop/renderer/App.tsx
- src/ui/desktop/renderer/index.html
- vite.config.ts

DELIVERABLE: React app renders
COMMIT: "[FRONTEND-SUB-2] Setup React base"
```

### Sub-Agent 3: WebSocket + State
**Task tool**:
```
Implementa WebSocket client e state management:

FILES:
- hooks/useWebSocket.ts (WS connection + reconnection)
- store.ts (Zustand store)

DELIVERABLE: WebSocket hook funzionante con store
COMMIT: "[FRONTEND-SUB-3] WebSocket + State"
```

---

## ⏸️ SYNC POINT 1

---

## 🚀 ONDATA 2: FEATURES

### Sub-Agent 4: Transcription + Insights
**Task tool**:
```
Implementa pannelli transcription e insights:

FILES:
- components/TranscriptionPanel.tsx
- components/InsightsPanel.tsx
- components/TranscriptionPanel.css

DELIVERABLE: 2 panels con real-time updates
COMMIT: "[FRONTEND-SUB-4] Transcription + Insights panels"
```

### Sub-Agent 5: Summary + Settings
**Task tool**:
```
Implementa pannelli summary e settings:

FILES:
- components/SummaryPanel.tsx
- components/SettingsPanel.tsx

DELIVERABLE: 2 panels completati
COMMIT: "[FRONTEND-SUB-5] Summary + Settings panels"
```

---

## ✅ VALIDAZIONE
```bash
npm run dev  # Test development mode
npm run build:win  # Build .exe
```

---

**FINE FRONTEND TEAM**
