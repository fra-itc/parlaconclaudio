import React, { useState, useEffect } from 'react';
import { useSettings, useStore } from '../store';
import { Button, Input, NumberInput, Toggle, Select } from './ui';

interface ValidationErrors {
  websocketUrl?: string;
  reconnectInterval?: string;
  maxReconnectAttempts?: string;
}

export const SettingsPanel: React.FC = () => {
  const settings = useSettings();
  const { updateSettings, resetSettings } = useStore();

  // Local form state
  const [formData, setFormData] = useState(settings);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Sync form data with store when settings change from outside
  useEffect(() => {
    setFormData(settings);
    setHasChanges(false);
  }, [settings]);

  // Validate WebSocket URL
  const validateUrl = (url: string): string | undefined => {
    if (!url.trim()) {
      return 'WebSocket URL is required';
    }
    try {
      const parsedUrl = new URL(url);
      if (parsedUrl.protocol !== 'ws:' && parsedUrl.protocol !== 'wss:') {
        return 'URL must use ws:// or wss:// protocol';
      }
    } catch {
      return 'Invalid URL format';
    }
    return undefined;
  };

  // Validate reconnect interval
  const validateReconnectInterval = (value: number): string | undefined => {
    if (value <= 0) {
      return 'Reconnect interval must be greater than 0';
    }
    if (value < 1000) {
      return 'Reconnect interval should be at least 1000ms (1 second)';
    }
    if (value > 60000) {
      return 'Reconnect interval should not exceed 60000ms (1 minute)';
    }
    return undefined;
  };

  // Validate max reconnect attempts
  const validateMaxReconnectAttempts = (value: number): string | undefined => {
    if (value <= 0) {
      return 'Max reconnect attempts must be greater than 0';
    }
    if (value > 100) {
      return 'Max reconnect attempts should not exceed 100';
    }
    return undefined;
  };

  // Handle form field changes
  const handleChange = (field: keyof typeof formData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
    setSaveSuccess(false);

    // Clear error for the field being edited
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  // Validate all fields
  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};

    const urlError = validateUrl(formData.websocketUrl);
    if (urlError) newErrors.websocketUrl = urlError;

    const intervalError = validateReconnectInterval(formData.reconnectInterval);
    if (intervalError) newErrors.reconnectInterval = intervalError;

    const attemptsError = validateMaxReconnectAttempts(formData.maxReconnectAttempts);
    if (attemptsError) newErrors.maxReconnectAttempts = attemptsError;

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle save
  const handleSave = () => {
    if (!validateForm()) {
      return;
    }

    updateSettings(formData);
    setHasChanges(false);
    setSaveSuccess(true);

    // Hide success message after 3 seconds
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  // Handle reset
  const handleReset = () => {
    if (window.confirm('Are you sure you want to reset all settings to their default values?')) {
      resetSettings();
      setSaveSuccess(false);
      setErrors({});
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 px-6 py-4">
        <h2 className="text-xl font-semibold">Settings</h2>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto p-6 space-y-8">
          {/* Save Success Banner */}
          {saveSuccess && (
            <div className="bg-green-900 border border-green-700 rounded-lg p-4 flex items-center gap-3">
              <svg
                className="w-5 h-5 text-green-400 flex-shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <p className="text-green-200 text-sm font-medium">
                Settings saved successfully!
              </p>
            </div>
          )}

          {/* Connection Settings Section */}
          <section>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-1">
                Connection Settings
              </h3>
              <p className="text-sm text-gray-400">
                Configure WebSocket connection and reconnection behavior
              </p>
            </div>

            <div className="space-y-4 bg-gray-800 rounded-lg p-5 border border-gray-700">
              <Input
                label="WebSocket URL"
                type="text"
                value={formData.websocketUrl}
                onChange={(e) => handleChange('websocketUrl', e.target.value)}
                error={errors.websocketUrl}
                helperText="The WebSocket server URL (e.g., ws://localhost:8000/ws)"
                placeholder="ws://localhost:8000/ws"
              />

              <div className="pt-2">
                <Toggle
                  label="Auto Reconnect"
                  checked={formData.autoReconnect}
                  onChange={(checked) => handleChange('autoReconnect', checked)}
                  helperText="Automatically attempt to reconnect when connection is lost"
                />
              </div>

              {formData.autoReconnect && (
                <>
                  <NumberInput
                    label="Reconnect Interval (ms)"
                    value={formData.reconnectInterval}
                    onChange={(e) => handleChange('reconnectInterval', parseInt(e.target.value) || 0)}
                    error={errors.reconnectInterval}
                    helperText="Time to wait between reconnection attempts (1000-60000ms)"
                    min={1000}
                    max={60000}
                    step={1000}
                  />

                  <NumberInput
                    label="Max Reconnect Attempts"
                    value={formData.maxReconnectAttempts}
                    onChange={(e) => handleChange('maxReconnectAttempts', parseInt(e.target.value) || 0)}
                    error={errors.maxReconnectAttempts}
                    helperText="Maximum number of reconnection attempts before giving up (1-100)"
                    min={1}
                    max={100}
                  />
                </>
              )}
            </div>
          </section>

          {/* UI Preferences Section */}
          <section>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-1">
                UI Preferences
              </h3>
              <p className="text-sm text-gray-400">
                Customize the appearance and behavior of the application
              </p>
            </div>

            <div className="space-y-4 bg-gray-800 rounded-lg p-5 border border-gray-700">
              <Select
                label="Theme"
                value={formData.theme}
                onChange={(e) => handleChange('theme', e.target.value as 'dark' | 'light')}
                options={[
                  { value: 'dark', label: 'Dark' },
                  { value: 'light', label: 'Light' },
                ]}
                helperText="Choose your preferred color theme"
              />

              <div className="pt-2">
                <Toggle
                  label="Enable Notifications"
                  checked={formData.notifications}
                  onChange={(checked) => handleChange('notifications', checked)}
                  helperText="Show desktop notifications for important events"
                />
              </div>

              <div className="pt-2">
                <Toggle
                  label="Auto Scroll"
                  checked={formData.autoScroll}
                  onChange={(checked) => handleChange('autoScroll', checked)}
                  helperText="Automatically scroll to latest transcription"
                />
              </div>
            </div>
          </section>

          {/* Audio Settings Section (Placeholder) */}
          <section>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-1">
                Audio Settings
              </h3>
              <p className="text-sm text-gray-400">
                Configure audio input and recording preferences
              </p>
            </div>

            <div className="bg-gray-800 rounded-lg p-5 border border-gray-700">
              <div className="flex items-center gap-3 text-gray-400">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="text-sm">
                  Audio input device selection will be available in a future update.
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="border-t border-gray-800 px-6 py-4 bg-gray-850">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <Button
            variant="danger"
            onClick={handleReset}
            disabled={!hasChanges && JSON.stringify(formData) === JSON.stringify(settings)}
          >
            Reset to Defaults
          </Button>
          <div className="flex gap-3">
            {hasChanges && (
              <span className="text-sm text-yellow-400 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                Unsaved changes
              </span>
            )}
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={!hasChanges}
            >
              Save Settings
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
