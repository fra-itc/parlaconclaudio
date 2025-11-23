/**
 * Electron API Test Component
 *
 * This component demonstrates how to use the Electron IPC API
 * in React components with TypeScript.
 */

import { useRecording, useWindowControls, useAppInfo, useAudioDevices } from '../hooks/useElectronAPI';

export function ElectronTest() {
  const { isRecording, error, startRecording, stopRecording } = useRecording();
  const { minimize, maximize, close, hide } = useWindowControls();
  const { version, platform, isDev } = useAppInfo();
  const { devices, loading, error: devicesError } = useAudioDevices();

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h2>Electron API Test</h2>

      {/* App Info */}
      <section style={{ marginBottom: '20px', padding: '10px', background: '#f0f0f0' }}>
        <h3>App Info</h3>
        <p>Version: {version}</p>
        <p>Platform: {platform}</p>
        <p>Development Mode: {isDev ? 'Yes' : 'No'}</p>
      </section>

      {/* Recording Controls */}
      <section style={{ marginBottom: '20px', padding: '10px', background: '#f0f0f0' }}>
        <h3>Recording</h3>
        <p>Status: {isRecording ? '🔴 Recording' : '⚫ Stopped'}</p>
        {error && <p style={{ color: 'red' }}>Error: {error}</p>}
        <button
          onClick={startRecording}
          disabled={isRecording}
          style={{ marginRight: '10px' }}
        >
          Start Recording
        </button>
        <button
          onClick={stopRecording}
          disabled={!isRecording}
        >
          Stop Recording
        </button>
      </section>

      {/* Audio Devices */}
      <section style={{ marginBottom: '20px', padding: '10px', background: '#f0f0f0' }}>
        <h3>Audio Devices</h3>
        {loading && <p>Loading devices...</p>}
        {devicesError && <p style={{ color: 'red' }}>Error: {devicesError}</p>}
        {devices.length > 0 ? (
          <ul>
            {devices.map((device) => (
              <li key={device.id}>
                {device.name} {device.isDefault && '(Default)'}
              </li>
            ))}
          </ul>
        ) : (
          <p>No devices found</p>
        )}
      </section>

      {/* Window Controls */}
      <section style={{ marginBottom: '20px', padding: '10px', background: '#f0f0f0' }}>
        <h3>Window Controls</h3>
        <button onClick={minimize} style={{ marginRight: '10px' }}>
          Minimize
        </button>
        <button onClick={maximize} style={{ marginRight: '10px' }}>
          Maximize
        </button>
        <button onClick={hide} style={{ marginRight: '10px' }}>
          Hide to Tray
        </button>
        <button onClick={close} style={{ marginRight: '10px', background: '#ff6b6b', color: 'white' }}>
          Close (to Tray)
        </button>
      </section>

      {/* Instructions */}
      <section style={{ marginBottom: '20px', padding: '10px', background: '#e3f2fd' }}>
        <h3>Instructions</h3>
        <ul>
          <li>Click "Start Recording" to test the recording API</li>
          <li>Window controls will minimize/maximize the window</li>
          <li>"Hide to Tray" will hide the window to system tray</li>
          <li>"Close" will also hide to tray (doesn't quit the app)</li>
          <li>Double-click the tray icon or use the tray menu to show the window again</li>
          <li>Use the tray menu "Quit" option to actually exit the application</li>
        </ul>
      </section>
    </div>
  );
}
