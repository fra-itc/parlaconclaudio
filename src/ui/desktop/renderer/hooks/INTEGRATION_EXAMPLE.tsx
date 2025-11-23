/**
 * INTEGRATION EXAMPLE: WebSocket Hook with Zustand Store
 *
 * This file demonstrates how to integrate the useWebSocket hook
 * with the Zustand store in your React components.
 *
 * Copy the relevant parts to your App.tsx or other components.
 */

import React, { useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import {
  useStore,
  useConnectionStatus,
  useConnectionError,
  useTranscription,
  useCurrentTranscription,
  useInsights,
  useCurrentSummary,
  useSettings,
} from '../store';

/**
 * Example 1: Simple WebSocket Connection Component
 * Use this in your App.tsx to establish WebSocket connection
 */
export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const settings = useSettings();

  // Initialize WebSocket connection
  const { isConnected, connectionStatus, error } = useWebSocket({
    url: settings.websocketUrl,
    autoConnect: true,
    autoReconnect: settings.autoReconnect,
    reconnectInterval: settings.reconnectInterval,
    maxReconnectAttempts: settings.maxReconnectAttempts,

    onOpen: () => {
      console.log('WebSocket connected successfully');
    },

    onClose: () => {
      console.log('WebSocket disconnected');
    },

    onError: (error) => {
      console.error('WebSocket error:', error);
    },
  });

  return (
    <>
      {children}
      {/* Optional: Add a connection status indicator */}
      <div style={{
        position: 'fixed',
        bottom: 10,
        right: 10,
        padding: '8px 12px',
        background: isConnected ? '#4caf50' : '#f44336',
        color: 'white',
        borderRadius: 4,
        fontSize: 12,
      }}>
        {connectionStatus}
        {error && ` - ${error}`}
      </div>
    </>
  );
};

/**
 * Example 2: Connection Control Component
 * Provides manual connection controls
 */
export const ConnectionControl: React.FC = () => {
  const connectionStatus = useConnectionStatus();
  const connectionError = useConnectionError();
  const settings = useSettings();
  const updateSettings = useStore((state) => state.updateSettings);

  const { isConnected, connect, disconnect } = useWebSocket({
    autoConnect: false,
  });

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    updateSettings({ websocketUrl: e.target.value });
  };

  return (
    <div style={{ padding: 20, background: '#2a2a2a', borderRadius: 8 }}>
      <h3>WebSocket Connection</h3>

      <div style={{ marginBottom: 15 }}>
        <label>
          WebSocket URL:
          <input
            type="text"
            value={settings.websocketUrl}
            onChange={handleUrlChange}
            style={{ marginLeft: 10, width: 300 }}
            disabled={isConnected}
          />
        </label>
      </div>

      <div style={{ marginBottom: 15 }}>
        <label>
          <input
            type="checkbox"
            checked={settings.autoReconnect}
            onChange={(e) => updateSettings({ autoReconnect: e.target.checked })}
          />
          {' '}Auto Reconnect
        </label>
      </div>

      <div style={{ marginBottom: 15 }}>
        <strong>Status:</strong> {connectionStatus}
        {connectionError && (
          <div style={{ color: '#f44336', marginTop: 5 }}>
            Error: {connectionError}
          </div>
        )}
      </div>

      <div>
        {!isConnected ? (
          <button onClick={connect} style={{ padding: '8px 16px', marginRight: 10 }}>
            Connect
          </button>
        ) : (
          <button onClick={disconnect} style={{ padding: '8px 16px', marginRight: 10 }}>
            Disconnect
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * Example 3: Transcription Display Component
 * Shows real-time and finalized transcriptions
 */
export const TranscriptionDisplay: React.FC = () => {
  const transcription = useTranscription();
  const currentTranscription = useCurrentTranscription();
  const settings = useSettings();
  const clearTranscription = useStore((state) => state.clearTranscription);

  // Auto-scroll to bottom when new segments arrive
  const transcriptRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (settings.autoScroll && transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcription, currentTranscription, settings.autoScroll]);

  return (
    <div style={{ padding: 20, background: '#1e1e1e', borderRadius: 8, height: 400 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
        <h3>Transcription</h3>
        <button onClick={clearTranscription}>Clear</button>
      </div>

      <div
        ref={transcriptRef}
        style={{
          height: 320,
          overflowY: 'auto',
          padding: 10,
          background: '#252525',
          borderRadius: 4,
        }}
      >
        {transcription.map((segment) => (
          <div
            key={segment.id}
            style={{
              marginBottom: 15,
              padding: 10,
              background: '#2a2a2a',
              borderRadius: 4,
              borderLeft: '3px solid #4caf50',
            }}
          >
            <div style={{ fontSize: 12, color: '#888', marginBottom: 5 }}>
              {new Date(segment.timestamp).toLocaleTimeString()}
              {segment.speaker && ` - ${segment.speaker}`}
              {segment.confidence && ` (${(segment.confidence * 100).toFixed(0)}%)`}
            </div>
            <div style={{ fontSize: 14, color: '#e0e0e0' }}>
              {segment.text}
            </div>
          </div>
        ))}

        {/* Current (not finalized) transcription */}
        {currentTranscription && (
          <div
            style={{
              padding: 10,
              background: '#2a2a2a',
              borderRadius: 4,
              borderLeft: '3px solid #ff9800',
              opacity: 0.7,
            }}
          >
            <div style={{ fontSize: 12, color: '#888', marginBottom: 5 }}>
              In progress...
            </div>
            <div style={{ fontSize: 14, color: '#e0e0e0', fontStyle: 'italic' }}>
              {currentTranscription}
            </div>
          </div>
        )}

        {transcription.length === 0 && !currentTranscription && (
          <div style={{ textAlign: 'center', color: '#666', padding: 40 }}>
            No transcription yet. Start speaking...
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Example 4: Insights Panel Component
 * Displays detected insights (keywords, entities, etc.)
 */
export const InsightsPanel: React.FC = () => {
  const insights = useInsights();
  const clearInsights = useStore((state) => state.clearInsights);

  const getInsightColor = (type: string) => {
    switch (type) {
      case 'keyword': return '#4caf50';
      case 'entity': return '#2196f3';
      case 'sentiment': return '#ff9800';
      case 'topic': return '#9c27b0';
      default: return '#666';
    }
  };

  return (
    <div style={{ padding: 20, background: '#1e1e1e', borderRadius: 8, height: 400 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
        <h3>Insights</h3>
        <button onClick={clearInsights}>Clear</button>
      </div>

      <div style={{ height: 320, overflowY: 'auto' }}>
        {insights.map((insight) => (
          <div
            key={insight.id}
            style={{
              marginBottom: 10,
              padding: 10,
              background: '#252525',
              borderRadius: 4,
              borderLeft: `3px solid ${getInsightColor(insight.type)}`,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
              <span
                style={{
                  fontSize: 11,
                  padding: '2px 8px',
                  background: getInsightColor(insight.type),
                  color: 'white',
                  borderRadius: 3,
                  textTransform: 'uppercase',
                }}
              >
                {insight.type}
              </span>
              <span style={{ fontSize: 11, color: '#888' }}>
                {new Date(insight.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <div style={{ fontSize: 14, color: '#e0e0e0' }}>
              {insight.content}
            </div>
            {insight.metadata && (
              <div style={{ fontSize: 11, color: '#666', marginTop: 5 }}>
                {JSON.stringify(insight.metadata)}
              </div>
            )}
          </div>
        ))}

        {insights.length === 0 && (
          <div style={{ textAlign: 'center', color: '#666', padding: 40 }}>
            No insights detected yet
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Example 5: Summary Display Component
 * Shows the generated summary
 */
export const SummaryDisplay: React.FC = () => {
  const currentSummary = useCurrentSummary();
  const summaries = useStore((state) => state.summaries);

  return (
    <div style={{ padding: 20, background: '#1e1e1e', borderRadius: 8 }}>
      <h3>Summary</h3>

      {currentSummary ? (
        <div style={{ padding: 15, background: '#252525', borderRadius: 4 }}>
          <div style={{ fontSize: 12, color: '#888', marginBottom: 10 }}>
            Generated at: {new Date(currentSummary.timestamp).toLocaleString()}
          </div>

          <div style={{ fontSize: 14, color: '#e0e0e0', lineHeight: 1.6, marginBottom: 15 }}>
            {currentSummary.content}
          </div>

          {currentSummary.keyPoints && currentSummary.keyPoints.length > 0 && (
            <div>
              <strong style={{ color: '#4caf50' }}>Key Points:</strong>
              <ul style={{ marginTop: 10, paddingLeft: 20 }}>
                {currentSummary.keyPoints.map((point, idx) => (
                  <li key={idx} style={{ color: '#e0e0e0', marginBottom: 5 }}>
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div style={{ textAlign: 'center', color: '#666', padding: 40 }}>
          No summary available yet
        </div>
      )}

      {summaries.length > 1 && (
        <div style={{ marginTop: 20, fontSize: 12, color: '#888' }}>
          {summaries.length} summaries generated
        </div>
      )}
    </div>
  );
};

/**
 * Example 6: Complete App Integration
 * Shows how to combine all components
 */
export const AppExample: React.FC = () => {
  return (
    <WebSocketProvider>
      <div style={{ padding: 20, background: '#121212', minHeight: '100vh' }}>
        <h1 style={{ color: '#fff', marginBottom: 20 }}>ORCHIDEA RTSTT</h1>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
          <ConnectionControl />
          <SummaryDisplay />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }}>
          <TranscriptionDisplay />
          <InsightsPanel />
        </div>
      </div>
    </WebSocketProvider>
  );
};

/**
 * HOW TO USE IN YOUR APP.TSX:
 *
 * import { useWebSocket } from '@hooks/useWebSocket';
 * import { useSettings } from './store';
 *
 * function App() {
 *   const settings = useSettings();
 *
 *   // Initialize WebSocket connection at the app level
 *   useWebSocket({
 *     url: settings.websocketUrl,
 *     autoConnect: true,
 *   });
 *
 *   return <div>Your app components here</div>;
 * }
 */
