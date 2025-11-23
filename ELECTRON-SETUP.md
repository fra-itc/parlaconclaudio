# Electron Setup Documentation

## Overview

This document describes the Electron desktop application setup for ORCHIDEA RTSTT (Real-Time Speech-to-Text). The setup includes:

- Electron main process with system tray integration
- Secure IPC communication using contextBridge
- React renderer process with Vite
- TypeScript support with type definitions
- Development and production build configurations

## Project Structure

```
RTSTT-frontend/
├── src/
│   ├── ui/
│   │   └── desktop/
│   │       ├── main.js              # Electron main process
│   │       ├── preload.js           # Preload script with contextBridge
│   │       ├── README.md            # Desktop app documentation
│   │       └── renderer/            # React renderer process
│   │           ├── index.html       # HTML entry point
│   │           ├── main.tsx         # React entry point
│   │           ├── App.tsx          # Main React component
│   │           ├── store.ts         # State management
│   │           ├── components/
│   │           │   └── ElectronTest.tsx  # API test component
│   │           └── hooks/
│   │               └── useElectronAPI.ts # React hooks for Electron API
│   └── types/
│       └── electron.d.ts            # TypeScript definitions for Electron API
├── assets/
│   └── README.md                    # Icon requirements documentation
├── package.json                     # Node.js dependencies and scripts
├── vite.config.ts                   # Vite configuration
├── tsconfig.json                    # TypeScript configuration
└── verify-electron.js               # Setup verification script

```

## Files Created

### 1. src/ui/desktop/main.js
**Purpose**: Electron main process - runs in Node.js environment

**Features**:
- BrowserWindow creation and lifecycle management
- System tray icon with context menu
- IPC handlers for renderer communication
- Development mode with DevTools
- Security best practices (contextIsolation, sandbox)

**Key IPC Handlers**:
- `recording:start` / `recording:stop` - Audio recording control
- `audio:get-devices` - Get available audio input devices
- `transcription:process` - Process audio for transcription
- `window:*` - Window control (minimize, maximize, close, hide, show)
- `settings:*` - Application settings management
- `app:get-version` / `app:get-path` - Application info

### 2. src/ui/desktop/preload.js
**Purpose**: Bridge between main and renderer processes with security

**Features**:
- Uses `contextBridge` to expose secure API to renderer
- Whitelisted IPC channels only
- No direct access to Node.js APIs from renderer
- TypeScript-friendly API design

**Exposed API**:
```javascript
window.electronAPI = {
  recording: { start(), stop() },
  audio: { getDevices(), updateSettings() },
  transcription: { process(), onUpdate() },
  window: { minimize(), maximize(), close(), hide(), show() },
  app: { getVersion(), getPath() },
  settings: { get(), update(), reset(), onChange() }
}
```

### 3. src/types/electron.d.ts
**Purpose**: TypeScript type definitions for Electron API

**Features**:
- Full TypeScript support for window.electronAPI
- Type safety in React components
- IntelliSense support in VS Code
- Interface definitions for all API methods

### 4. src/ui/desktop/renderer/hooks/useElectronAPI.ts
**Purpose**: React hooks for accessing Electron API

**Hooks Provided**:
- `useElectronAPI()` - Check API availability
- `useRecording()` - Recording functionality
- `useAudioDevices()` - Audio device management
- `useWindowControls()` - Window control functions
- `useAppInfo()` - Application information
- `useTranscription()` - Transcription with real-time updates

### 5. src/ui/desktop/renderer/components/ElectronTest.tsx
**Purpose**: Test component demonstrating Electron API usage

**Features**:
- Interactive UI for testing all IPC handlers
- Recording start/stop controls
- Audio device listing
- Window control buttons
- App info display

### 6. package.json (Updated)
**Changes Made**:
- `main`: Set to `src/ui/desktop/main.js`
- `type`: Changed to `commonjs` (required for Electron main process)
- Added dependencies:
  - `electron-builder` (^25.1.8)
  - `concurrently` (^9.2.1)
  - `cross-env` (^7.0.3)
- Added scripts:
  - `start`: Launch Electron directly
  - `dev`: Run Vite and Electron concurrently
  - `dev:vite`: Start Vite dev server
  - `dev:electron`: Start Electron in dev mode
  - `build:electron`: Package Electron app
  - `build:all`: Build renderer and package app
- Added `build` configuration for electron-builder

### 7. verify-electron.js
**Purpose**: Automated verification of Electron setup

**Checks**:
- Required files existence
- package.json configuration
- main.js features (BrowserWindow, Tray, IPC)
- preload.js security (contextBridge, contextIsolation)
- Dependencies installation

## Security Features

1. **Context Isolation**: Enabled - renderer and main processes are isolated
2. **Node Integration**: Disabled - renderer cannot access Node.js directly
3. **Sandbox**: Enabled - additional security layer
4. **Content Security Policy**: Set in index.html
5. **Whitelisted IPC Channels**: Only allowed channels are exposed
6. **contextBridge**: Secure API exposure to renderer

## Development Workflow

### Running the Application

#### Option 1: Development Mode (Recommended)
```bash
npm run dev
```
This starts both Vite dev server (port 5173) and Electron with:
- Hot module replacement
- DevTools automatically opened
- Live reload on file changes

#### Option 2: Start Electron Only
```bash
npm start
```
Launches Electron with current build (no hot reload)

### Building for Production

```bash
# Build renderer (React/Vite)
npm run build

# Package Electron app
npm run build:electron

# Or do both
npm run build:all
```

Output:
- `dist/renderer/` - Built React application
- `dist-electron/` - Packaged Electron application

### Platform-Specific Builds

The electron-builder configuration supports:
- **Windows**: NSIS installer and portable executable
- **macOS**: DMG and ZIP
- **Linux**: AppImage and DEB

## Usage Examples

### Using Electron API in React Components

```typescript
import { useRecording, useWindowControls } from './hooks/useElectronAPI';

function MyComponent() {
  const { isRecording, startRecording, stopRecording } = useRecording();
  const { minimize, close } = useWindowControls();

  return (
    <div>
      <button onClick={startRecording}>Start</button>
      <button onClick={stopRecording}>Stop</button>
      <button onClick={minimize}>Minimize</button>
    </div>
  );
}
```

### Direct API Access

```typescript
// Check if API is available
if (window.electronAPI) {
  // Get app version
  const version = await window.electronAPI.app.getVersion();

  // Get audio devices
  const { devices } = await window.electronAPI.audio.getDevices();

  // Start recording
  await window.electronAPI.recording.start();
}
```

## System Tray Features

The application includes a system tray icon with:
- **Show/Hide** window options
- **Recording status** indicator (checkbox)
- **Quit** option to exit application
- **Double-click** tray icon to toggle window visibility

When the window is closed, it minimizes to tray instead of quitting.

## Next Steps

1. **Add Icons**
   - Create icon files in `assets/` directory
   - See `assets/README.md` for requirements
   - Recommended: 1024x1024 PNG for base, generate other formats

2. **Implement Audio Recording**
   - Replace mock handlers in `main.js` with actual recording logic
   - Consider using `node-mic` or `node-audio-recorder`
   - Implement audio streaming to ML backend

3. **Connect to Backend**
   - Add HTTP/WebSocket client for ML API
   - Implement transcription processing
   - Handle real-time transcription updates

4. **Settings Persistence**
   - Add `electron-store` for settings storage
   - Implement actual settings handlers in main.js
   - Create settings UI in renderer

5. **Auto-Updates**
   - Configure `electron-updater`
   - Add update check on app start
   - Implement update notification UI

6. **Additional Features**
   - Global keyboard shortcuts (`globalShortcut`)
   - System notifications
   - Context menu integration
   - Custom title bar (frameless window)

## Troubleshooting

### Electron Won't Start

**Symptoms**: App crashes immediately or doesn't launch

**Solutions**:
1. Verify `main` field in package.json points to correct file
2. Check Node.js version (requires >= 18)
3. Run verification script: `node verify-electron.js`
4. Check console for error messages

### IPC Not Working

**Symptoms**: Renderer cannot call Electron API

**Solutions**:
1. Open DevTools and check for `window.electronAPI`
2. Verify preload script is loaded (check console logs in dev mode)
3. Ensure channels are whitelisted in preload.js
4. Check for CSP violations in DevTools

### Renderer Not Loading

**Symptoms**: Blank window or "Cannot GET /" error

**Solutions**:
1. Ensure Vite dev server is running (port 5173)
2. Check `vite.config.ts` paths are correct
3. In production, verify `dist/renderer` directory exists
4. Check main.js `loadURL`/`loadFile` paths

### Build Fails

**Symptoms**: electron-builder errors

**Solutions**:
1. Ensure all files in `build.files` array exist
2. Add icon files to assets/
3. Check electron-builder logs for specific errors
4. Try clearing `dist-electron/` and rebuilding

## Verification

Run the automated verification script:

```bash
node verify-electron.js
```

This checks:
- File existence
- package.json configuration
- Security settings
- IPC setup
- Dependencies

All checks should pass (20/20).

## Dependencies Installed

**Production**:
- `react` (^18.3.1)
- `react-dom` (^18.3.1)

**Development**:
- `electron` (^31.2.0)
- `electron-builder` (^25.1.8)
- `concurrently` (^9.2.1)
- `cross-env` (^7.0.3)
- `vite` (^5.3.3)
- `@vitejs/plugin-react` (^4.3.1)
- `typescript` (^5.5.3)
- Plus TypeScript and ESLint tooling

## Resources

- [Electron Documentation](https://www.electronjs.org/docs)
- [Electron Security](https://www.electronjs.org/docs/tutorial/security)
- [electron-builder](https://www.electron.build/)
- [Vite Documentation](https://vitejs.dev/)

## Support

For issues or questions:
1. Check this documentation
2. Run `node verify-electron.js` to diagnose problems
3. Review Electron and Vite logs
4. Check `src/ui/desktop/README.md` for detailed API documentation

---

**Setup Complete**: ✅ All 20 verification checks passed
**Ready to Run**: `npm start` or `npm run dev`
**Commit Message**: `[FRONTEND-SUB-1] Setup Electron main process and IPC`
