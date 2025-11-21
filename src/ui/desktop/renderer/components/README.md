# RTSTT Frontend Components

This directory contains the React components for the ORCHIDEA RTSTT (Real-Time Speech-to-Text) frontend application.

## Overview

The components are organized into several categories:

- **Main Panels**: Core UI panels (Summary, Settings)
- **UI Components**: Reusable form and interface elements
- **Examples**: Integration examples and test utilities

## Main Components

### SummaryPanel

Displays transcription summaries with key points and history.

**Features:**
- Current/Latest summary display with highlighting
- Key points as bullet list
- Summary history (collapsible)
- Copy to clipboard functionality
- Empty state handling
- Timestamp formatting
- Summary selection from history

**Usage:**
```tsx
import { SummaryPanel } from './components';

function App() {
  return <SummaryPanel />;
}
```

**State Management:**
- Uses `useSummaries()` for all summaries
- Uses `useCurrentSummary()` for active summary
- Uses `setCurrentSummary()` to select from history

### SettingsPanel

Configuration panel for application settings.

**Features:**
- Connection settings (WebSocket URL, reconnection)
- UI preferences (theme, notifications, auto-scroll)
- Form validation
- Save/Reset functionality
- Visual feedback for changes
- Persistence via Zustand store

**Usage:**
```tsx
import { SettingsPanel } from './components';

function App() {
  return <SettingsPanel />;
}
```

**Validation Rules:**
- WebSocket URL: Must be valid ws:// or wss:// URL
- Reconnect Interval: 1000-60000ms
- Max Reconnect Attempts: 1-100

## UI Components

Located in `./ui/`, these are reusable form components with consistent styling:

### Button

```tsx
<Button
  variant="primary" // 'primary' | 'secondary' | 'danger'
  size="medium"     // 'small' | 'medium' | 'large'
  onClick={handleClick}
>
  Click Me
</Button>
```

### Input

```tsx
<Input
  label="Username"
  value={username}
  onChange={(e) => setUsername(e.target.value)}
  error={errors.username}
  helperText="Enter your username"
/>
```

### NumberInput

```tsx
<NumberInput
  label="Port"
  value={port}
  onChange={(e) => setPort(parseInt(e.target.value))}
  min={1000}
  max={65535}
  error={errors.port}
/>
```

### Toggle

```tsx
<Toggle
  label="Enable Feature"
  checked={enabled}
  onChange={setEnabled}
  helperText="Toggle this feature on or off"
/>
```

### Select

```tsx
<Select
  label="Theme"
  value={theme}
  onChange={(e) => setTheme(e.target.value)}
  options={[
    { value: 'dark', label: 'Dark' },
    { value: 'light', label: 'Light' }
  ]}
/>
```

## Examples and Testing

### SUMMARY_SETTINGS_EXAMPLE.tsx

Contains four different layout examples for integrating the panels:

1. **TabbedPanelExample**: Tab-based navigation
2. **SideBySidePanelExample**: Split-screen layout
3. **SidebarPanelExample**: Collapsible sidebar
4. **ModalPanelExample**: Modal overlay approach

**Usage:**
```tsx
import { TabbedPanelExample } from './components/SUMMARY_SETTINGS_EXAMPLE';

function App() {
  return <TabbedPanelExample />;
}
```

### TestDataGenerator

Utility component for generating sample data to test the panels.

**Features:**
- Generate 4 sample summaries with timestamps
- Add single summary on demand
- Clear summaries or all data
- Test scenarios guide

**Usage:**
```tsx
import { TestDataGenerator } from './components';

function TestPage() {
  return (
    <div>
      <TestDataGenerator />
      <SummaryPanel />
    </div>
  );
}
```

## Styling

All components use Tailwind CSS with a dark theme:

**Color Palette:**
- Background: `bg-gray-900`, `bg-gray-800`
- Borders: `border-gray-800`, `border-gray-700`
- Text: `text-white`, `text-gray-300`, `text-gray-400`
- Primary: `bg-blue-600`, `hover:bg-blue-700`
- Success: `bg-green-900`, `text-green-200`
- Danger: `bg-red-600`, `hover:bg-red-700`

**Focus States:**
- All interactive elements have focus rings for accessibility
- Focus ring: `focus:ring-2 focus:ring-blue-500`

## Integration Guide

### Quick Start

1. **Import components:**
```tsx
import { SummaryPanel, SettingsPanel } from './components';
```

2. **Choose a layout** from the examples or create your own

3. **Add test data** (development only):
```tsx
import { TestDataGenerator } from './components';
```

4. **Use the store** to manage state:
```tsx
import { useStore, useSummaries, useSettings } from './store';
```

### Example Integration

```tsx
import React, { useState } from 'react';
import { SummaryPanel, SettingsPanel } from './components';

function App() {
  const [view, setView] = useState<'summary' | 'settings'>('summary');

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      <header className="border-b border-gray-800 px-6 py-4">
        <nav className="flex gap-4">
          <button onClick={() => setView('summary')}>Summary</button>
          <button onClick={() => setView('settings')}>Settings</button>
        </nav>
      </header>

      <main className="flex-1 overflow-hidden">
        {view === 'summary' && <SummaryPanel />}
        {view === 'settings' && <SettingsPanel />}
      </main>
    </div>
  );
}
```

## State Management

The components use Zustand for state management. Key selectors:

```tsx
// Summaries
const summaries = useSummaries();
const currentSummary = useCurrentSummary();

// Settings
const settings = useSettings();

// Actions
const {
  addSummary,
  setCurrentSummary,
  updateSettings,
  resetSettings
} = useStore();
```

## TypeScript

All components are fully typed. Key interfaces:

```typescript
interface Summary {
  id: string;
  content: string;
  timestamp: number;
  keyPoints?: string[];
}

interface Settings {
  websocketUrl: string;
  autoReconnect: boolean;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  theme: 'dark' | 'light';
  notifications: boolean;
  autoScroll: boolean;
}
```

## Accessibility

Components follow accessibility best practices:

- Semantic HTML elements
- ARIA attributes where needed
- Keyboard navigation support
- Focus management
- Screen reader friendly
- High contrast ratios

## Future Enhancements

- [ ] Markdown rendering for summary content
- [ ] Audio input device selection
- [ ] Export summaries (PDF, TXT, MD)
- [ ] Summary search and filtering
- [ ] Dark/Light theme implementation
- [ ] Keyboard shortcuts
- [ ] Summary tags/categories
- [ ] Custom notification settings

## File Structure

```
components/
├── SummaryPanel.tsx              # Main summary display panel
├── SettingsPanel.tsx             # Settings configuration panel
├── SUMMARY_SETTINGS_EXAMPLE.tsx  # Integration examples
├── TestDataGenerator.tsx         # Test data utility
├── index.ts                      # Component exports
├── README.md                     # This file
└── ui/                          # Reusable UI components
    ├── Button.tsx
    ├── Input.tsx
    ├── NumberInput.tsx
    ├── Toggle.tsx
    ├── Select.tsx
    └── index.ts
```

## Contributing

When adding new components:

1. Follow the existing TypeScript patterns
2. Use Tailwind CSS for styling
3. Include proper TypeScript types
4. Add accessibility features
5. Document props and usage
6. Update this README

## Support

For issues or questions about these components, refer to:
- Main project documentation
- Zustand store documentation (`../store.ts`)
- Tailwind CSS documentation
