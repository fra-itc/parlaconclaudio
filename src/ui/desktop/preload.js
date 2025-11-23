const { contextBridge, ipcRenderer } = require('electron');

/**
 * Preload script - Context Bridge for secure IPC communication
 *
 * This script runs in the renderer process but has access to Node.js APIs.
 * We use contextBridge to expose a limited, secure API to the renderer process.
 *
 * Security best practices:
 * - Never expose the entire ipcRenderer object
 * - Only expose specific channels that are needed
 * - Validate all inputs from the renderer
 * - Use invoke/handle pattern for request-response communication
 */

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // ============================================================================
  // Recording API
  // ============================================================================
  recording: {
    /**
     * Start audio recording
     * @returns {Promise<{success: boolean, message: string}>}
     */
    start: () => ipcRenderer.invoke('recording:start'),

    /**
     * Stop audio recording
     * @returns {Promise<{success: boolean, message: string}>}
     */
    stop: () => ipcRenderer.invoke('recording:stop'),
  },

  // ============================================================================
  // Audio API
  // ============================================================================
  audio: {
    /**
     * Get available audio input devices
     * @returns {Promise<{success: boolean, devices: Array}>}
     */
    getDevices: () => ipcRenderer.invoke('audio:get-devices'),

    /**
     * Update audio settings
     * @param {Object} settings - Audio configuration settings
     * @returns {Promise<{success: boolean}>}
     */
    updateSettings: (settings) => ipcRenderer.invoke('settings:update-audio', settings),
  },

  // ============================================================================
  // Transcription API
  // ============================================================================
  transcription: {
    /**
     * Process audio data for transcription
     * @param {ArrayBuffer|Blob} audioData - Audio data to transcribe
     * @returns {Promise<{success: boolean, text: string, confidence: number}>}
     */
    process: (audioData) => ipcRenderer.invoke('transcription:process', audioData),

    /**
     * Listen for real-time transcription updates
     * @param {Function} callback - Callback function to receive updates
     * @returns {Function} Cleanup function to remove the listener
     */
    onUpdate: (callback) => {
      const subscription = (event, data) => callback(data);
      ipcRenderer.on('transcription:update', subscription);

      // Return cleanup function
      return () => {
        ipcRenderer.removeListener('transcription:update', subscription);
      };
    },
  },

  // ============================================================================
  // Window Control API
  // ============================================================================
  window: {
    /**
     * Minimize the window
     */
    minimize: () => ipcRenderer.invoke('window:minimize'),

    /**
     * Maximize/unmaximize the window
     */
    maximize: () => ipcRenderer.invoke('window:maximize'),

    /**
     * Close the window (will minimize to tray)
     */
    close: () => ipcRenderer.invoke('window:close'),

    /**
     * Hide the window to system tray
     */
    hide: () => ipcRenderer.invoke('window:hide'),

    /**
     * Show the window from system tray
     */
    show: () => ipcRenderer.invoke('window:show'),

    /**
     * Listen for window state changes
     * @param {Function} callback - Callback function
     * @returns {Function} Cleanup function
     */
    onStateChange: (callback) => {
      const subscription = (event, state) => callback(state);
      ipcRenderer.on('window:state-change', subscription);
      return () => {
        ipcRenderer.removeListener('window:state-change', subscription);
      };
    },
  },

  // ============================================================================
  // Application API
  // ============================================================================
  app: {
    /**
     * Get application version
     * @returns {Promise<string>}
     */
    getVersion: () => ipcRenderer.invoke('app:get-version'),

    /**
     * Get application path
     * @param {string} name - Path name (userData, temp, etc.)
     * @returns {Promise<string>}
     */
    getPath: (name) => ipcRenderer.invoke('app:get-path', name),

    /**
     * Listen for app events
     * @param {string} channel - Event channel name
     * @param {Function} callback - Callback function
     * @returns {Function} Cleanup function
     */
    on: (channel, callback) => {
      const validChannels = ['app:update-available', 'app:update-downloaded'];
      if (!validChannels.includes(channel)) {
        throw new Error(`Invalid channel: ${channel}`);
      }

      const subscription = (event, ...args) => callback(...args);
      ipcRenderer.on(channel, subscription);

      return () => {
        ipcRenderer.removeListener(channel, subscription);
      };
    },
  },

  // ============================================================================
  // Settings API
  // ============================================================================
  settings: {
    /**
     * Get all settings
     * @returns {Promise<Object>}
     */
    get: () => ipcRenderer.invoke('settings:get'),

    /**
     * Update settings
     * @param {Object} settings - Settings to update
     * @returns {Promise<{success: boolean}>}
     */
    update: (settings) => ipcRenderer.invoke('settings:update', settings),

    /**
     * Reset settings to defaults
     * @returns {Promise<{success: boolean}>}
     */
    reset: () => ipcRenderer.invoke('settings:reset'),

    /**
     * Listen for settings changes
     * @param {Function} callback - Callback function
     * @returns {Function} Cleanup function
     */
    onChange: (callback) => {
      const subscription = (event, settings) => callback(settings);
      ipcRenderer.on('settings:changed', subscription);
      return () => {
        ipcRenderer.removeListener('settings:changed', subscription);
      };
    },
  },

  // ============================================================================
  // Utility Functions
  // ============================================================================

  /**
   * Check if running in development mode
   * @returns {boolean}
   */
  isDev: () => process.env.NODE_ENV === 'development',

  /**
   * Get platform information
   * @returns {string}
   */
  platform: process.platform,

  /**
   * Send a generic message to main process (use with caution)
   * @param {string} channel - Channel name
   * @param {any} data - Data to send
   */
  send: (channel, data) => {
    // Whitelist of allowed channels
    const validChannels = ['ping', 'log'];
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  },

  /**
   * Invoke a generic handler (use with caution)
   * @param {string} channel - Channel name
   * @param {any} args - Arguments to pass
   * @returns {Promise<any>}
   */
  invoke: (channel, ...args) => {
    // Whitelist of allowed channels
    const validChannels = [];
    if (validChannels.includes(channel)) {
      return ipcRenderer.invoke(channel, ...args);
    }
    throw new Error(`Channel '${channel}' is not allowed`);
  },
});

// Log that preload script has loaded (only in development)
if (process.env.NODE_ENV === 'development') {
  console.log('[Preload] Context bridge initialized');
  console.log('[Preload] Available APIs:', Object.keys(window.electronAPI || {}));
}

// Expose a simple API check for debugging
contextBridge.exposeInMainWorld('__electronAPIVersion', '1.0.0');
