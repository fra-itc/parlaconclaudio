# WebSocket Hook Usage Guide

## Overview

The `useWebSocket` hook provides a robust WebSocket client with automatic reconnection, error handling, and integration with the Zustand store.

## Basic Usage

```typescript
import { useWebSocket } from '@hooks/useWebSocket';

function MyComponent() {
  const { isConnected, connect, disconnect, send, connectionStatus, error } = useWebSocket({
    url: 'ws://localhost:8000/ws',
    autoConnect: true,
    autoReconnect: true,
  });

  return (
    <div>
      <p>Status: {connectionStatus}</p>
      {error && <p>Error: {error}</p>}
      <button onClick={connect} disabled={isConnected}>Connect</button>
      <button onClick={disconnect} disabled={!isConnected}>Disconnect</button>
    </div>
  );
}
```

## Features

### 1. Automatic Reconnection
- Exponential backoff strategy
- Configurable max attempts and intervals
- Jitter to prevent thundering herd

### 2. Connection Management
- Manual connect/disconnect
- Auto-connect on mount
- Proper cleanup on unmount

### 3. Heartbeat/Ping-Pong
- Automatic ping every 30 seconds
- Keeps connection alive
- Detects dead connections

### 4. Message Handling
The hook automatically handles these message types:
- `transcription_update`: Real-time transcription updates
- `transcription_segment`: Finalized transcription segments
- `insight_detected`: New insights (keywords, entities, etc.)
- `summary_ready`: Generated summaries
- `error`: Server-side errors
- `ping`/`pong`: Heartbeat messages

### 5. Store Integration
All received data is automatically synchronized with the Zustand store:
- Transcription segments
- Current transcription text
- Insights
- Summaries
- Connection status
- Errors

## API

### Options

```typescript
interface UseWebSocketOptions {
  url?: string;                      // WebSocket URL (defaults to settings.websocketUrl)
  autoConnect?: boolean;             // Auto-connect on mount (default: true)
  autoReconnect?: boolean;           // Auto-reconnect on disconnect (default: from settings)
  reconnectInterval?: number;        // Base reconnect delay in ms (default: from settings)
  maxReconnectAttempts?: number;     // Max reconnection attempts (default: from settings)
  onOpen?: () => void;               // Callback on connection open
  onClose?: () => void;              // Callback on connection close
  onError?: (error: Event) => void;  // Callback on error
  onMessage?: (message: WebSocketMessage) => void; // Callback on message
}
```

### Return Value

```typescript
interface UseWebSocketReturn {
  isConnected: boolean;       // True if connected
  connect: () => void;        // Connect to WebSocket
  disconnect: () => void;     // Disconnect from WebSocket
  send: (message: any) => void; // Send message (auto-serializes objects)
  connectionStatus: string;   // Current status: 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error'
  error: string | null;       // Last error message
}
```

## Message Format

### Incoming Messages

```typescript
interface WebSocketMessage {
  type: 'transcription_update' | 'transcription_segment' | 'insight_detected' | 'summary_ready' | 'error' | 'ping' | 'pong';
  data?: any;
  timestamp?: number;
}
```

#### Examples

**Transcription Update (real-time, not finalized)**
```json
{
  "type": "transcription_update",
  "data": {
    "text": "This is what the user is currently saying..."
  },
  "timestamp": 1700000000000
}
```

**Transcription Segment (finalized)**
```json
{
  "type": "transcription_segment",
  "data": {
    "id": "segment-123",
    "text": "This is a completed sentence.",
    "timestamp": 1700000000000,
    "speaker": "Speaker 1",
    "confidence": 0.95
  }
}
```

**Insight Detected**
```json
{
  "type": "insight_detected",
  "data": {
    "id": "insight-456",
    "type": "keyword",
    "content": "project deadline",
    "timestamp": 1700000000000,
    "metadata": {
      "importance": "high"
    }
  }
}
```

**Summary Ready**
```json
{
  "type": "summary_ready",
  "data": {
    "id": "summary-789",
    "content": "Discussion about project timeline and deliverables...",
    "timestamp": 1700000000000,
    "keyPoints": [
      "Deadline extended to next Friday",
      "Need 3 more developers",
      "Budget approved"
    ]
  }
}
```

### Outgoing Messages

Send messages using the `send` function:

```typescript
// Send a simple command
send({ type: 'start_recording' });

// Send with data
send({
  type: 'configure',
  data: {
    language: 'en-US',
    sampleRate: 16000
  }
});
```

## Advanced Usage

### Custom Event Handlers

```typescript
const { isConnected } = useWebSocket({
  onOpen: () => {
    console.log('Connected to WebSocket!');
    // Send initial configuration
    send({ type: 'configure', data: { language: 'en-US' } });
  },
  onClose: () => {
    console.log('Disconnected from WebSocket');
  },
  onError: (error) => {
    console.error('WebSocket error:', error);
  },
  onMessage: (message) => {
    console.log('Received message:', message);
  }
});
```

### Using with Store Selectors

```typescript
import { useConnectionStatus, useTranscription, useInsights } from '../store';

function Dashboard() {
  const connectionStatus = useConnectionStatus();
  const transcription = useTranscription();
  const insights = useInsights();

  useWebSocket({ autoConnect: true });

  return (
    <div>
      <p>Status: {connectionStatus}</p>
      <p>Segments: {transcription.length}</p>
      <p>Insights: {insights.length}</p>
    </div>
  );
}
```

### Manual Connection Control

```typescript
function ConnectionManager() {
  const { isConnected, connect, disconnect } = useWebSocket({
    autoConnect: false, // Don't auto-connect
  });

  const handleConnect = () => {
    connect();
  };

  const handleDisconnect = () => {
    disconnect();
  };

  return (
    <div>
      {!isConnected ? (
        <button onClick={handleConnect}>Connect</button>
      ) : (
        <button onClick={handleDisconnect}>Disconnect</button>
      )}
    </div>
  );
}
```

## Reconnection Strategy

The hook implements an exponential backoff strategy:

1. First attempt: Immediate
2. Second attempt: ~3 seconds (configurable)
3. Third attempt: ~6 seconds
4. Fourth attempt: ~12 seconds
5. ...up to max 30 seconds between attempts

Each delay includes random jitter (0-1 second) to prevent multiple clients from reconnecting simultaneously.

## Error Handling

The hook handles several error scenarios:

1. **Connection Failure**: Automatically retries with backoff
2. **Message Parsing Error**: Logs error and sets connection error state
3. **Send Failure**: Logs error and sets connection error state
4. **Max Reconnect Attempts**: Sets status to 'error' after max attempts

## Configuration via Settings

You can configure default WebSocket behavior through the settings in the store:

```typescript
import { useStore } from '../store';

function SettingsPanel() {
  const { settings, updateSettings } = useStore();

  const handleUpdateUrl = (url: string) => {
    updateSettings({ websocketUrl: url });
  };

  const handleToggleAutoReconnect = () => {
    updateSettings({ autoReconnect: !settings.autoReconnect });
  };

  return (
    <div>
      <input
        value={settings.websocketUrl}
        onChange={(e) => handleUpdateUrl(e.target.value)}
      />
      <label>
        <input
          type="checkbox"
          checked={settings.autoReconnect}
          onChange={handleToggleAutoReconnect}
        />
        Auto Reconnect
      </label>
    </div>
  );
}
```

## Best Practices

1. **Single Instance**: Use the hook only once per app (in App.tsx or a top-level component)
2. **Settings First**: Configure WebSocket URL in settings before connecting
3. **Error Display**: Show connection errors to users
4. **Manual Controls**: Provide UI for manual connect/disconnect
5. **Cleanup**: The hook automatically cleans up on unmount, no manual cleanup needed

## Troubleshooting

### Connection keeps disconnecting
- Check if the server is running
- Verify the WebSocket URL is correct
- Check server logs for errors
- Ensure firewall isn't blocking WebSocket connections

### Messages not being received
- Check browser console for parsing errors
- Verify message format matches expected schema
- Check if connection status is 'connected'

### Reconnection not working
- Verify `autoReconnect` is enabled
- Check if max reconnection attempts has been reached
- Look for connection errors in the store
