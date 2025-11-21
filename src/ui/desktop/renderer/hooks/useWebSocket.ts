import { useEffect, useRef, useCallback } from 'react';
import { useStore } from '../store';
import type { TranscriptionSegment, Insight, Summary } from '../store';

export interface WebSocketMessage {
  type: 'transcription_update' | 'transcription_segment' | 'insight_detected' | 'summary_ready' | 'error' | 'ping' | 'pong';
  data?: any;
  timestamp?: number;
}

export interface UseWebSocketOptions {
  url?: string;
  autoConnect?: boolean;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  send: (message: any) => void;
  connectionStatus: string;
  error: string | null;
}

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    url: customUrl,
    autoConnect = true,
    autoReconnect: customAutoReconnect,
    reconnectInterval: customReconnectInterval,
    maxReconnectAttempts: customMaxReconnectAttempts,
    onOpen,
    onClose,
    onError,
    onMessage,
  } = options;

  // Get store state and actions
  const settings = useStore((state) => state.settings);
  const connectionStatus = useStore((state) => state.connectionStatus);
  const connectionError = useStore((state) => state.connectionError);
  const reconnectAttempts = useStore((state) => state.reconnectAttempts);

  const setConnectionStatus = useStore((state) => state.setConnectionStatus);
  const setConnectionError = useStore((state) => state.setConnectionError);
  const setLastConnectedAt = useStore((state) => state.setLastConnectedAt);
  const incrementReconnectAttempts = useStore((state) => state.incrementReconnectAttempts);
  const resetReconnectAttempts = useStore((state) => state.resetReconnectAttempts);

  const addTranscriptionSegment = useStore((state) => state.addTranscriptionSegment);
  const updateCurrentTranscription = useStore((state) => state.updateCurrentTranscription);
  const addInsight = useStore((state) => state.addInsight);
  const addSummary = useStore((state) => state.addSummary);

  // Use custom options or fall back to settings
  const wsUrl = customUrl || settings.websocketUrl;
  const shouldAutoReconnect = customAutoReconnect ?? settings.autoReconnect;
  const reconnectDelay = customReconnectInterval ?? settings.reconnectInterval;
  const maxAttempts = customMaxReconnectAttempts ?? settings.maxReconnectAttempts;

  // Refs for WebSocket and reconnection
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Calculate exponential backoff delay
  const getReconnectDelay = useCallback((attempt: number): number => {
    const baseDelay = reconnectDelay;
    const maxDelay = 30000; // 30 seconds max
    const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
    // Add jitter to prevent thundering herd
    return delay + Math.random() * 1000;
  }, [reconnectDelay]);

  // Handle incoming messages
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      // Call custom onMessage handler if provided
      if (onMessage) {
        onMessage(message);
      }

      // Handle different message types
      switch (message.type) {
        case 'transcription_update':
          // Real-time transcription update (not finalized)
          if (message.data?.text) {
            updateCurrentTranscription(message.data.text);
          }
          break;

        case 'transcription_segment':
          // Finalized transcription segment
          if (message.data) {
            const segment: TranscriptionSegment = {
              id: message.data.id || `segment-${Date.now()}`,
              text: message.data.text,
              timestamp: message.data.timestamp || Date.now(),
              speaker: message.data.speaker,
              confidence: message.data.confidence,
            };
            addTranscriptionSegment(segment);
          }
          break;

        case 'insight_detected':
          // New insight detected
          if (message.data) {
            const insight: Insight = {
              id: message.data.id || `insight-${Date.now()}`,
              type: message.data.type || 'keyword',
              content: message.data.content,
              timestamp: message.data.timestamp || Date.now(),
              metadata: message.data.metadata,
            };
            addInsight(insight);
          }
          break;

        case 'summary_ready':
          // Summary generated
          if (message.data) {
            const summary: Summary = {
              id: message.data.id || `summary-${Date.now()}`,
              content: message.data.content,
              timestamp: message.data.timestamp || Date.now(),
              keyPoints: message.data.keyPoints,
            };
            addSummary(summary);
          }
          break;

        case 'error':
          // Server error
          console.error('WebSocket server error:', message.data);
          setConnectionError(message.data?.message || 'Server error');
          break;

        case 'pong':
          // Pong response to ping
          break;

        default:
          console.warn('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
      setConnectionError('Failed to parse message');
    }
  }, [onMessage, updateCurrentTranscription, addTranscriptionSegment, addInsight, addSummary, setConnectionError]);

  // Setup ping/pong heartbeat
  const setupHeartbeat = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }

    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        try {
          wsRef.current.send(JSON.stringify({ type: 'ping' }));
        } catch (error) {
          console.error('Error sending ping:', error);
        }
      }
    }, 30000); // Ping every 30 seconds
  }, []);

  // Cleanup heartbeat
  const cleanupHeartbeat = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    // Cleanup existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    try {
      setConnectionStatus('connecting');
      setConnectionError(null);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        setConnectionError(null);
        setLastConnectedAt(Date.now());
        resetReconnectAttempts();
        setupHeartbeat();

        if (onOpen) {
          onOpen();
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason);
        cleanupHeartbeat();

        if (connectionStatus === 'connected') {
          setConnectionStatus('disconnected');
        }

        if (onClose) {
          onClose();
        }

        // Attempt reconnection if enabled and not a normal closure
        if (shouldAutoReconnect && event.code !== 1000 && reconnectAttempts < maxAttempts) {
          const delay = getReconnectDelay(reconnectAttempts);
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxAttempts})`);

          setConnectionStatus('reconnecting');
          incrementReconnectAttempts();

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectAttempts >= maxAttempts) {
          setConnectionError(`Failed to reconnect after ${maxAttempts} attempts`);
          setConnectionStatus('error');
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setConnectionError('Connection error occurred');
        setConnectionStatus('error');

        if (onError) {
          onError(event);
        }
      };

      ws.onmessage = handleMessage;

    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setConnectionError('Failed to create WebSocket connection');
      setConnectionStatus('error');
    }
  }, [
    wsUrl,
    shouldAutoReconnect,
    maxAttempts,
    reconnectAttempts,
    connectionStatus,
    setConnectionStatus,
    setConnectionError,
    setLastConnectedAt,
    resetReconnectAttempts,
    incrementReconnectAttempts,
    getReconnectDelay,
    setupHeartbeat,
    cleanupHeartbeat,
    handleMessage,
    onOpen,
    onClose,
    onError,
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    cleanupHeartbeat();

    // Close WebSocket connection
    if (wsRef.current) {
      // Use code 1000 for normal closure to prevent auto-reconnect
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }

    setConnectionStatus('disconnected');
    resetReconnectAttempts();
  }, [setConnectionStatus, resetReconnectAttempts, cleanupHeartbeat]);

  // Send message through WebSocket
  const send = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        const data = typeof message === 'string' ? message : JSON.stringify(message);
        wsRef.current.send(data);
      } catch (error) {
        console.error('Error sending message:', error);
        setConnectionError('Failed to send message');
      }
    } else {
      console.warn('WebSocket is not connected. Message not sent.');
      setConnectionError('WebSocket is not connected');
    }
  }, [setConnectionError]);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      cleanupHeartbeat();
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount');
      }
    };
  }, []); // Only run on mount/unmount

  return {
    isConnected: connectionStatus === 'connected',
    connect,
    disconnect,
    send,
    connectionStatus,
    error: connectionError,
  };
};

export default useWebSocket;
