const { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === 'development';

let mainWindow = null;
let tray = null;

// Configuration for the main window
const WINDOW_CONFIG = {
  width: 1200,
  height: 800,
  minWidth: 800,
  minHeight: 600,
  webPreferences: {
    preload: path.join(__dirname, 'preload.js'),
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
  },
  icon: path.join(__dirname, '../../../assets/icon.png'),
  show: false, // Don't show until ready-to-show event
};

/**
 * Create the main application window
 */
function createWindow() {
  mainWindow = new BrowserWindow(WINDOW_CONFIG);

  // Load the app - in production load index.html, in dev load from Vite dev server
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173'); // Default Vite dev server port
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../../../dist/index.html'));
  }

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  // Handle window close - minimize to tray instead of quitting
  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
    return false;
  });

  // Window closed cleanup
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Log any navigation errors
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('Failed to load:', errorCode, errorDescription);
  });
}

/**
 * Create system tray icon with menu
 */
function createTray() {
  // Create a simple icon (you'll need to replace this with your actual icon)
  const iconPath = path.join(__dirname, '../../../assets/tray-icon.png');

  // Fallback to a native image if icon doesn't exist
  let trayIcon;
  try {
    trayIcon = nativeImage.createFromPath(iconPath);
    if (trayIcon.isEmpty()) {
      throw new Error('Icon is empty');
    }
  } catch (error) {
    console.warn('Tray icon not found, using default');
    // Create a simple 16x16 bitmap as fallback
    trayIcon = nativeImage.createEmpty();
  }

  tray = new Tray(trayIcon);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show App',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        } else {
          createWindow();
        }
      },
    },
    {
      label: 'Hide App',
      click: () => {
        if (mainWindow) {
          mainWindow.hide();
        }
      },
    },
    { type: 'separator' },
    {
      label: 'Recording Status',
      type: 'checkbox',
      checked: false,
      enabled: false, // Will be enabled via IPC
      id: 'recording-status',
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.isQuitting = true;
        app.quit();
      },
    },
  ]);

  tray.setToolTip('RTSTT - Real-Time Speech-to-Text');
  tray.setContextMenu(contextMenu);

  // Double-click to show window
  tray.on('double-click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
        mainWindow.focus();
      }
    } else {
      createWindow();
    }
  });
}

/**
 * Update tray menu recording status
 */
function updateRecordingStatus(isRecording) {
  if (tray) {
    const menu = tray.getContextMenu();
    const recordingItem = menu.getMenuItemById('recording-status');
    if (recordingItem) {
      recordingItem.checked = isRecording;
      recordingItem.enabled = true;
    }
  }
}

// ============================================================================
// IPC Handlers - Communication between main and renderer processes
// ============================================================================

/**
 * Handle recording start request from renderer
 */
ipcMain.handle('recording:start', async (event) => {
  console.log('Recording start requested');
  updateRecordingStatus(true);

  // Here you would implement actual recording logic
  // For now, just return success
  return { success: true, message: 'Recording started' };
});

/**
 * Handle recording stop request from renderer
 */
ipcMain.handle('recording:stop', async (event) => {
  console.log('Recording stop requested');
  updateRecordingStatus(false);

  return { success: true, message: 'Recording stopped' };
});

/**
 * Handle audio settings update
 */
ipcMain.handle('settings:update-audio', async (event, settings) => {
  console.log('Audio settings updated:', settings);

  // Store settings (you might want to use electron-store or similar)
  // For now, just acknowledge
  return { success: true };
});

/**
 * Get system audio devices
 */
ipcMain.handle('audio:get-devices', async (event) => {
  console.log('Audio devices requested');

  // This would typically use node-mic or similar to get actual devices
  // For now, return mock data
  return {
    success: true,
    devices: [
      { id: 'default', name: 'Default Microphone', isDefault: true },
      { id: 'device1', name: 'Microphone (USB)', isDefault: false },
    ],
  };
});

/**
 * Handle transcription request
 */
ipcMain.handle('transcription:process', async (event, audioData) => {
  console.log('Transcription requested for audio data');

  // This would connect to your ML backend
  // For now, return mock response
  return {
    success: true,
    text: 'Mock transcription result',
    confidence: 0.95,
  };
});

/**
 * Window control handlers
 */
ipcMain.handle('window:minimize', () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.handle('window:maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.handle('window:close', () => {
  if (mainWindow) mainWindow.close();
});

ipcMain.handle('window:hide', () => {
  if (mainWindow) mainWindow.hide();
});

ipcMain.handle('window:show', () => {
  if (mainWindow) {
    mainWindow.show();
    mainWindow.focus();
  }
});

/**
 * Get app version
 */
ipcMain.handle('app:get-version', () => {
  return app.getVersion();
});

/**
 * Get app paths
 */
ipcMain.handle('app:get-path', (event, name) => {
  return app.getPath(name);
});

// ============================================================================
// App Lifecycle Events
// ============================================================================

// This method will be called when Electron has finished initialization
app.whenReady().then(() => {
  createWindow();
  createTray();

  // On macOS, re-create window when dock icon is clicked and no windows are open
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    } else if (mainWindow) {
      mainWindow.show();
    }
  });
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Before quit cleanup
app.on('before-quit', () => {
  app.isQuitting = true;
});

// Handle errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
});

// Development mode helpers
if (isDev) {
  console.log('Running in development mode');
  console.log('Main process file:', __filename);
  console.log('Preload script:', path.join(__dirname, 'preload.js'));
}
