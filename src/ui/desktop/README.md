# RTSTT Electron Desktop Application

This directory contains the Electron main process and IPC configuration for the RTSTT desktop application.

## Structure

```
src/ui/desktop/
├── main.js          # Electron main process (Node.js environment)
├── preload.js       # Preload script with contextBridge (secure IPC)
└── renderer/        # React renderer process (browser environment)
    ├── index.html
    ├── main.tsx     # React entry point
    ├── App.tsx      # Main React component
    └── store.ts     # State management
```

## Main Process (main.js)

The main process handles:
- **BrowserWindow** creation and management
- **System Tray** icon and menu
- **IPC handlers** for communication with renderer
- **Development tools** in dev mode
- **Window lifecycle** events

### Features

1. **System Tray Integration**
   - Tray icon with context menu
   - Show/Hide window
   - Recording status indicator
   - Quit application

2. **IPC Communication**
   - `recording:start` - Start audio recording
   - `recording:stop` - Stop audio recording
   - `audio:get-devices` - Get available audio devices
   - `transcription:process` - Process audio for transcription
   - `window:*` - Window control commands
   - `settings:*` - Application settings

3. **Development Mode**
   - Loads from Vite dev server (http://localhost:5173)
   - Opens DevTools automatically
   - Hot module replacement support

## Preload Script (preload.js)

The preload script uses `contextBridge` to expose a secure API to the renderer process.

### Exposed APIs

All APIs are available via `window.electronAPI`:

```typescript
// Recording API
window.electronAPI.recording.start()
window.electronAPI.recording.stop()

// Audio API
window.electronAPI.audio.getDevices()
window.electronAPI.audio.updateSettings(settings)

// Transcription API
window.electronAPI.transcription.process(audioData)
window.electronAPI.transcription.onUpdate(callback)

// Window Control API
window.electronAPI.window.minimize()
window.electronAPI.window.maximize()
window.electronAPI.window.close()
window.electronAPI.window.hide()
window.electronAPI.window.show()

// Application API
window.electronAPI.app.getVersion()
window.electronAPI.app.getPath(name)

// Settings API
window.electronAPI.settings.get()
window.electronAPI.settings.update(settings)
window.electronAPI.settings.reset()
```

## Security

The preload script implements several security best practices:

1. **Context Isolation** - Enabled by default
2. **Node Integration** - Disabled in renderer
3. **Sandbox** - Enabled for renderer process
4. **Whitelisted Channels** - Only specific IPC channels are exposed
5. **Input Validation** - All inputs from renderer are validated

## Usage

### Development

```bash
# Start Vite dev server and Electron
npm run dev

# Or start separately
npm run dev:vite    # Start Vite dev server on port 5173
npm run dev:electron # Start Electron in development mode
```

### Production Build

```bash
# Build renderer and package Electron app
npm run build:all

# Or separately
npm run build           # Build Vite/React app
npm run build:electron  # Package Electron app
```

### Direct Electron Start

```bash
# Start Electron with current files
npm start
```

## Configuration

### package.json

- `main`: Points to `src/ui/desktop/main.js`
- `type`: Set to `commonjs` for Electron compatibility

### vite.config.ts

- Root: `src/ui/desktop/renderer`
- Output: `dist/renderer`
- Dev server: Port 5173

## Build Output

- `dist/renderer/` - Built React application
- `dist-electron/` - Packaged Electron application

## Platform Support

- **Windows**: NSIS installer and portable executable
- **macOS**: DMG and ZIP distributions
- **Linux**: AppImage and DEB packages

## Adding New IPC Handlers

1. Add handler in `main.js`:
```javascript
ipcMain.handle('my-channel', async (event, data) => {
  // Handle request
  return { success: true, result: data };
});
```

2. Expose in `preload.js`:
```javascript
contextBridge.exposeInMainWorld('electronAPI', {
  myApi: {
    myMethod: (data) => ipcRenderer.invoke('my-channel', data),
  },
});
```

3. Use in renderer:
```typescript
const result = await window.electronAPI.myApi.myMethod(data);
```

## Troubleshooting

### Electron won't start
- Check that `main` field in package.json points to correct file
- Verify Node.js version >= 18
- Check console for errors

### IPC not working
- Verify preload script is loaded (check DevTools console)
- Check that channels are whitelisted in preload.js
- Ensure contextBridge is exposing the API correctly

### Renderer not loading
- Check Vite dev server is running on port 5173
- Verify CORS is enabled in vite.config.ts
- Check for CSP violations in DevTools console

## Next Steps

- Implement actual audio recording functionality
- Connect to ML backend for transcription
- Add settings persistence (electron-store)
- Implement auto-updates
- Add keyboard shortcuts (globalShortcut)
