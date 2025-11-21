/**
 * React hook for accessing Electron IPC API
 *
 * This hook provides a safe way to access the Electron API in React components
 * with proper TypeScript typing and error handling.
 */

import { useEffect, useState } from 'react';

/**
 * Check if Electron API is available
 */
export function useElectronAPI() {
  const [isAvailable, setIsAvailable] = useState(false);

  useEffect(() => {
    setIsAvailable(typeof window !== 'undefined' && !!window.electronAPI);
  }, []);

  return {
    isAvailable,
    api: isAvailable ? window.electronAPI : null,
  };
}

/**
 * Hook for recording functionality
 */
export function useRecording() {
  const { api, isAvailable } = useElectronAPI();
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startRecording = async () => {
    if (!isAvailable || !api) {
      setError('Electron API not available');
      return;
    }

    try {
      const result = await api.recording.start();
      if (result.success) {
        setIsRecording(true);
        setError(null);
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start recording');
    }
  };

  const stopRecording = async () => {
    if (!isAvailable || !api) {
      setError('Electron API not available');
      return;
    }

    try {
      const result = await api.recording.stop();
      if (result.success) {
        setIsRecording(false);
        setError(null);
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop recording');
    }
  };

  return {
    isRecording,
    error,
    startRecording,
    stopRecording,
  };
}

/**
 * Hook for audio devices
 */
export function useAudioDevices() {
  const { api, isAvailable } = useElectronAPI();
  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDevices = async () => {
    if (!isAvailable || !api) {
      setError('Electron API not available');
      return;
    }

    setLoading(true);
    try {
      const result = await api.audio.getDevices();
      if (result.success) {
        setDevices(result.devices);
        setError(null);
      } else {
        setError('Failed to fetch devices');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch devices');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAvailable) {
      fetchDevices();
    }
  }, [isAvailable]);

  return {
    devices,
    loading,
    error,
    refetch: fetchDevices,
  };
}

/**
 * Hook for window controls
 */
export function useWindowControls() {
  const { api, isAvailable } = useElectronAPI();

  const minimize = () => api?.window.minimize();
  const maximize = () => api?.window.maximize();
  const close = () => api?.window.close();
  const hide = () => api?.window.hide();
  const show = () => api?.window.show();

  return {
    isAvailable,
    minimize,
    maximize,
    close,
    hide,
    show,
  };
}

/**
 * Hook for app info
 */
export function useAppInfo() {
  const { api, isAvailable } = useElectronAPI();
  const [version, setVersion] = useState<string>('');
  const [platform, setPlatform] = useState<string>('');

  useEffect(() => {
    if (isAvailable && api) {
      api.app.getVersion().then(setVersion);
      setPlatform(api.platform);
    }
  }, [isAvailable, api]);

  return {
    version,
    platform,
    isDev: api?.isDev() ?? false,
  };
}

/**
 * Hook for transcription with real-time updates
 */
export function useTranscription() {
  const { api, isAvailable } = useElectronAPI();
  const [transcription, setTranscription] = useState<string>('');
  const [confidence, setConfidence] = useState<number>(0);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    if (!isAvailable || !api) return;

    // Subscribe to real-time updates
    const cleanup = api.transcription.onUpdate((data) => {
      setTranscription(data.text);
      setConfidence(data.confidence);
    });

    return cleanup;
  }, [isAvailable, api]);

  const processAudio = async (audioData: ArrayBuffer | Blob) => {
    if (!isAvailable || !api) {
      console.error('Electron API not available');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await api.transcription.process(audioData);
      if (result.success) {
        setTranscription(result.text);
        setConfidence(result.confidence);
      }
    } catch (err) {
      console.error('Transcription failed:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  return {
    transcription,
    confidence,
    isProcessing,
    processAudio,
  };
}
