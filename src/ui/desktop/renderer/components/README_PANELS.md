# TranscriptionPanel & InsightsPanel

**Real-time transcription and insights display components for ORCHIDEA RTSTT**

## Overview

These components provide a professional, feature-rich UI for displaying real-time speech transcription and AI-generated insights. Both panels automatically connect to the Zustand store and receive live updates from the WebSocket connection.

## Components

### 1. TranscriptionPanel

**File:** `TranscriptionPanel.tsx` (336 lines)

#### Features
- **Real-time Display**: Shows current transcription as it's being spoken with a "speaking..." indicator
- **Finalized Segments**: Scrollable history of completed transcription segments
- **Auto-scroll**: Automatically scrolls to show latest content (respects user settings)
- **Metadata Display**:
  - Timestamp (formatted as HH:MM:SS)
  - Speaker identification (when available)
  - Confidence level with color-coding:
    - Green (High): ≥90%
    - Orange (Medium): 70-89%
    - Red (Low): <70%
- **Empty State**: User-friendly message when no transcriptions are available
- **Accessibility**: Full ARIA labels and semantic HTML
- **Styling**: Dark theme with monospace font for better readability

#### Store Integration
```tsx
import { useTranscription, useCurrentTranscription } from '../store';

const transcription = useTranscription();         // Array of finalized segments
const currentTranscription = useCurrentTranscription(); // Current real-time text
```

#### Visual Features
- Pulsing green dot animation for "speaking" indicator
- Hover effects on segments
- Smooth scrolling
- Custom scrollbar styling
- Responsive layout

---

### 2. InsightsPanel

**File:** `InsightsPanel.tsx` (401 lines)

#### Features
- **Type Filtering**: Toggle between all insights or filter by specific type
- **Color-coded Badges**:
  - **Keyword** (Blue): Important keywords from transcription
  - **Entity** (Green): Named entities (people, places, products)
  - **Sentiment** (Orange/Red/Green): Emotional tone analysis
  - **Topic** (Purple): Main topics discussed
- **Dynamic Sentiment Colors**:
  - Green: Positive sentiment
  - Red: Negative sentiment
  - Orange: Neutral sentiment
- **Metadata Display**: Shows additional context for each insight
- **Fade-in Animation**: New insights smoothly fade in
- **Empty State**: Contextual messages for no insights or filtered results
- **Accessibility**: Full ARIA labels and semantic HTML

#### Store Integration
```tsx
import { useInsights } from '../store';

const insights = useInsights(); // Array of all insights
```

#### Visual Features
- Smooth fade-in animation for new insights (0.5s)
- Interactive filter buttons with hover/active states
- Hover effects on insight cards
- Custom scrollbar styling
- Badge count showing total insights
- Emoji icons for each insight type

---

## Integration Examples

### Quick Start

```tsx
import TranscriptionPanel from './components/TranscriptionPanel';
import InsightsPanel from './components/InsightsPanel';

const App = () => {
  return (
    <div style={{ display: 'flex', gap: '16px', padding: '16px', height: '100vh' }}>
      <div style={{ flex: 1 }}>
        <TranscriptionPanel />
      </div>
      <div style={{ flex: 1 }}>
        <InsightsPanel />
      </div>
    </div>
  );
};
```

### Example Layouts

See `PANEL_INTEGRATION_EXAMPLE.tsx` for 5 complete layout examples:

1. **SideBySideLayout**: Equal split (50/50) - Best for wide screens
2. **StackedLayout**: Vertical stack - Good for narrow screens
3. **AsymmetricLayout**: 70/30 split - More space for transcription
4. **TabbedLayout**: Toggle between panels - Space-efficient
5. **ResponsiveLayout**: Auto-switch based on screen width

### Test with Mock Data

To test the panels with simulated real-time data:

```tsx
import TestPanelsWithMockData from './components/TestPanelsWithMockData';

const App = () => {
  return <TestPanelsWithMockData />;
};
```

This will simulate:
- Typing effect for current transcription
- Automatic finalization of segments
- Random speaker assignment
- Random confidence levels
- Periodic insight generation
- Continuous loop

---

## Styling

### Design System

Both panels follow a consistent dark theme:

```css
Background:       #1e1e1e
Panel Background: #252526
Panel Header:     #2d2d30
Borders:          #3e3e42
Text Primary:     #ffffff
Text Secondary:   #e0e0e0
Text Muted:       #858585
```

### Type Colors

**Insights:**
- Keyword: `#2196f3` (Blue)
- Entity: `#4caf50` (Green)
- Sentiment: `#ff9800` (Orange) / dynamic based on sentiment
- Topic: `#9c27b0` (Purple)

**Confidence:**
- High (≥90%): `#4caf50` (Green)
- Medium (70-89%): `#ff9800` (Orange)
- Low (<70%): `#f44336` (Red)

### Fonts

- **UI Text**: System font stack (sans-serif)
- **Transcription**: `'Consolas', 'Monaco', 'Courier New', monospace`
- **Timestamps**: Monospace for alignment

---

## Store Requirements

Both panels require the Zustand store with the following structure:

```typescript
// From store.ts
export interface TranscriptionSegment {
  id: string;
  text: string;
  timestamp: number;
  speaker?: string;
  confidence?: number;
}

export interface Insight {
  id: string;
  type: 'keyword' | 'entity' | 'sentiment' | 'topic';
  content: string;
  timestamp: number;
  metadata?: Record<string, any>;
}

// Store state
interface AppState {
  transcription: TranscriptionSegment[];
  currentTranscription: string;
  insights: Insight[];
  settings: {
    autoScroll: boolean;
    // ... other settings
  };
}

// Selectors
export const useTranscription = () => useStore((state) => state.transcription);
export const useCurrentTranscription = () => useStore((state) => state.currentTranscription);
export const useInsights = () => useStore((state) => state.insights);
export const useSettings = () => useStore((state) => state.settings);
```

---

## WebSocket Integration

The panels automatically receive updates from the WebSocket through the store. No direct WebSocket handling is needed in the panels themselves.

**Expected WebSocket messages:**

```typescript
// Current transcription (real-time)
{
  type: 'transcription_interim',
  data: { text: 'Hello world...' }
}

// Finalized segment
{
  type: 'transcription_final',
  data: {
    id: 'seg-123',
    text: 'Hello world.',
    timestamp: 1732220000000,
    speaker: 'Speaker A',
    confidence: 0.95
  }
}

// Insight
{
  type: 'insight',
  data: {
    id: 'insight-456',
    type: 'keyword',
    content: 'Hello',
    timestamp: 1732220000000,
    metadata: { frequency: 3 }
  }
}
```

---

## Accessibility

Both components follow accessibility best practices:

- **Semantic HTML**: Using `<header>`, `<main>`, `<section>`, `<article>`, etc.
- **ARIA Labels**: All interactive elements and regions have proper labels
- **ARIA Roles**: `role="region"`, `role="article"`, `role="list"`, etc.
- **ARIA States**: `aria-pressed` for toggle buttons
- **Keyboard Navigation**: All interactive elements are keyboard accessible
- **Time Elements**: Using `<time>` with `dateTime` attribute for timestamps
- **Color Contrast**: All text meets WCAG AA standards for readability

---

## Performance Considerations

### TranscriptionPanel
- Uses `useRef` for scroll container to avoid unnecessary re-renders
- Auto-scroll only triggers when enabled in settings
- Hover state managed with local state to avoid store updates

### InsightsPanel
- Filter logic runs on the client (no store updates)
- Animation IDs tracked with Set for efficient lookups
- Animations automatically cleaned up after completion

### Both Panels
- Minimal re-renders using Zustand selectors
- No expensive computations in render
- Efficient CSS animations (transform/opacity only)
- Optimized scrollbar styling (GPU-accelerated)

---

## Browser Compatibility

- **Chrome/Edge**: Fully supported (Chromium-based)
- **Firefox**: Fully supported
- **Safari**: Fully supported (webkit scrollbar prefixes included)
- **Electron**: Fully supported (Chromium-based)

Note: Custom scrollbar styling uses `-webkit-scrollbar` which works in Chromium and Safari. Firefox uses native scrollbar styling.

---

## Future Enhancements

Potential features for future iterations:

### TranscriptionPanel
- [ ] Search/filter transcription history
- [ ] Export transcription to text/JSON
- [ ] Copy individual segments to clipboard
- [ ] Highlight keywords from insights
- [ ] Customizable font size
- [ ] Speaker color coding
- [ ] Timestamp jump navigation

### InsightsPanel
- [ ] Sort by timestamp/type/relevance
- [ ] Detailed view modal for insights
- [ ] Export insights to CSV/JSON
- [ ] Link insights to related transcription segments
- [ ] Confidence scores for insights
- [ ] Insight trends over time
- [ ] Custom insight type definitions

---

## Troubleshooting

### Panels not updating
**Issue:** Panels show empty state even when data is in store
**Solution:** Verify WebSocket is connected and store actions are being called

### Auto-scroll not working
**Issue:** Panel doesn't scroll to latest content
**Solution:** Check `settings.autoScroll` is `true` in store

### TypeScript errors
**Issue:** Type mismatch errors in IDE
**Solution:** Ensure all store types are properly exported and imported

### Performance issues
**Issue:** UI lags with many segments/insights
**Solution:** Implement virtualization for large lists (future enhancement)

---

## File Structure

```
src/ui/desktop/renderer/components/
├── TranscriptionPanel.tsx          # Main transcription display component
├── InsightsPanel.tsx               # Main insights display component
├── PANEL_INTEGRATION_EXAMPLE.tsx   # 5 example layouts for integration
├── TestPanelsWithMockData.tsx      # Test component with simulated data
└── README_PANELS.md                # This file
```

---

## Quick Reference

### Component Import
```tsx
import TranscriptionPanel from './components/TranscriptionPanel';
import InsightsPanel from './components/InsightsPanel';
```

### Store Selectors
```tsx
import { useTranscription, useCurrentTranscription, useInsights } from './store';
```

### Example Usage
```tsx
<div style={{ display: 'flex', height: '100vh', gap: '16px', padding: '16px' }}>
  <TranscriptionPanel />
  <InsightsPanel />
</div>
```

---

## Credits

**Component Design:** Dark theme inspired by VS Code
**Icons:** Unicode emoji characters (cross-platform compatible)
**Animation:** CSS3 keyframes for smooth transitions
**State Management:** Zustand store with React hooks
**TypeScript:** Full type safety with strict mode

---

## License

Part of the ORCHIDEA RTSTT project. See project LICENSE for details.
