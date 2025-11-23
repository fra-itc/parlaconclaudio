# TERMINAL 3: MUI Frontend Development

**Branch:** `feature/mui-frontend`
**Worktree:** `/home/frisco/projects/RTSTT-frontend`
**Estimated Time:** 4-6 hours
**Priority:** HIGH

## Objective
Build a beautiful, minimal, and stylish frontend using Material-UI (MUI) with real-time audio visualization, transcription display, and metrics dashboard.

---

## Task Checklist

### Phase 1: MUI Setup & Dependencies (30 min)

- [ ] Navigate to frontend directory:
  ```bash
  cd src/ui/desktop/renderer
  ```

- [ ] Install MUI v5 and dependencies:
  ```bash
  npm install @mui/material @emotion/react @emotion/styled
  npm install @mui/icons-material
  npm install @mui/x-charts  # For metrics charts
  npm install recharts  # Additional charting library
  ```

- [ ] Install audio visualization dependencies:
  ```bash
  npm install wavesurfer.js  # Audio waveform visualization
  npm install react-audio-visualize  # React audio components
  ```

- [ ] Verify installation:
  ```bash
  npm list | grep -E "(mui|emotion|chart|wave)"
  ```

### Phase 2: Theme System (45 min)

- [ ] Create theme configuration (`src/ui/desktop/renderer/theme.ts`):
  ```typescript
  // Define dark and light themes
  // Configure color palette (primary, secondary, background)
  // Set typography (Roboto font)
  // Configure component overrides
  // Add custom breakpoints
  ```

- [ ] Create theme context provider (`src/ui/desktop/renderer/contexts/ThemeContext.tsx`):
  - Implement theme toggle (dark/light)
  - Persist theme preference to localStorage
  - Provide theme state to all components

- [ ] Test theme switching:
  - Dark mode looks professional
  - Light mode is readable
  - All components respond to theme changes

### Phase 3: Main Application Layout (60 min)

- [ ] Create AppLayout component (`src/ui/desktop/renderer/components/Layout/AppLayout.tsx`):
  ```typescript
  // MUI AppBar with title and controls
  // Sidebar navigation (optional)
  // Main content area
  // Status bar at bottom
  // Theme toggle button
  ```

- [ ] Structure layout sections:
  ```
  ┌─────────────────────────────────────┐
  │  AppBar (Title, Controls, Theme)    │
  ├─────────────────────────────────────┤
  │ ┌──────────┬────────────────────┐  │
  │ │          │                    │  │
  │ │  Audio   │   Transcription    │  │
  │ │  Visual  │   Panel            │  │
  │ │          │                    │  │
  │ ├──────────┼────────────────────┤  │
  │ │          │                    │  │
  │ │ Insights │   Summary          │  │
  │ │ Panel    │   Panel            │  │
  │ │          │                    │  │
  │ └──────────┴────────────────────┘  │
  ├─────────────────────────────────────┤
  │  Status Bar (Metrics, Connection)   │
  └─────────────────────────────────────┘
  ```

- [ ] Implement responsive grid:
  - Desktop: 2x2 grid layout
  - Tablet: Stack panels vertically
  - Mobile: Single column

### Phase 4: Audio Visualizer Component (60 min)

- [ ] Create AudioVisualizer (`src/ui/desktop/renderer/components/AudioVisualizer/AudioVisualizer.tsx`):
  ```typescript
  // Real-time waveform display
  // Audio level meter (VU meter)
  // VAD status indicator
  // Recording state (idle/listening/processing)
  ```

- [ ] Features to implement:
  - Live audio waveform using WaveSurfer.js
  - Color-coded audio levels (green/yellow/red)
  - Smooth animations
  - Responsive canvas sizing

- [ ] Add controls:
  - Start/Stop recording button (MUI Fab)
  - Microphone selection dropdown
  - Volume control slider
  - Mute/unmute toggle

- [ ] Style with MUI:
  - Card component for container
  - Paper elevation for depth
  - Smooth transitions
  - Clean minimal design

### Phase 5: Enhanced Transcription Panel (60 min)

- [ ] Update TranscriptionPanel with MUI:
  ```typescript
  // Use MUI Card for container
  // MUI Typography for text
  // Add word-level highlighting
  // Show speaker labels (if diarization enabled)
  // Display confidence scores
  ```

- [ ] Implement real-time updates:
  - Auto-scroll as new text arrives
  - Highlight current word being spoken
  - Fade-in animation for new segments
  - Color-code by speaker

- [ ] Add features:
  - Search within transcription
  - Export to text file (MUI IconButton)
  - Copy to clipboard button
  - Clear transcription button

- [ ] Styling:
  - Monospace font for transcription
  - Comfortable line spacing
  - Subtle background color
  - Smooth scrolling

### Phase 6: Enhanced Insights Panel (45 min)

- [ ] Update InsightsPanel with MUI components:
  ```typescript
  // MUI Chip for keywords
  // MUI List for entities
  // MUI Accordion for sections
  // Color-coded sentiment indicator
  ```

- [ ] Organize insights:
  - Keywords section (top 10 with MUI Chips)
  - Named entities (Person, Org, Location)
  - Sentiment analysis (with emotion emoji)
  - Key phrases extraction

- [ ] Add visual indicators:
  - Sentiment gauge (MUI CircularProgress styled)
  - Entity type icons
  - Keyword frequency badges
  - Confidence scores

### Phase 7: Enhanced Summary Panel (45 min)

- [ ] Update SummaryPanel with MUI:
  ```typescript
  // MUI Card with elevation
  // MUI Typography for formatted text
  // MUI Accordion for bullet points
  // Loading skeleton while generating
  ```

- [ ] Improve summary display:
  - Formatted markdown rendering
  - Bullet point lists
  - Key takeaways section
  - Action items (if detected)

- [ ] Add controls:
  - Regenerate summary button
  - Copy summary button
  - Export to PDF (future)
  - Summary length selector

### Phase 8: Metrics Dashboard Component (60 min)

- [ ] Create MetricsDashboard (`src/ui/desktop/renderer/components/MetricsDashboard/MetricsDashboard.tsx`):
  ```typescript
  // Real-time metrics display
  // Processing latency chart
  // Audio quality indicators
  // System resource usage
  ```

- [ ] Metrics to display:
  - STT latency (ms)
  - NLP processing time (ms)
  - Summary generation time (ms)
  - Total pipeline latency
  - Audio quality score
  - WebSocket connection status

- [ ] Use MUI X Charts:
  - Line chart for latency over time
  - Gauge for audio quality
  - Bar chart for processing stages
  - Sparklines for trends

- [ ] Add to status bar:
  - Connection status badge
  - Latency indicator (green/yellow/red)
  - Model status (loaded/loading/error)

### Phase 9: Settings Panel (Optional - 30 min)

- [ ] Create SettingsPanel with MUI:
  - Audio input device selection
  - Model selection (Whisper large-v3, etc.)
  - Language selection
  - Enable/disable features
  - Theme preference
  - Keyboard shortcuts

- [ ] Use MUI components:
  - Select for dropdowns
  - Switch for toggles
  - Slider for numeric values
  - Tabs for categories

### Phase 10: Polish & Animations (45 min)

- [ ] Add smooth transitions:
  - Fade-in for new content
  - Slide-in for panels
  - Pulse for active recording
  - Ripple effects on buttons

- [ ] Improve UX:
  - Loading states (MUI Skeleton)
  - Error boundaries
  - Empty states (MUI Typography + Icon)
  - Success/error notifications (MUI Snackbar)

- [ ] Accessibility:
  - ARIA labels
  - Keyboard navigation
  - Focus indicators
  - Screen reader support

### Phase 11: Integration & Testing (30 min)

- [ ] Update App.tsx to use new layout:
  ```typescript
  import { ThemeProvider } from '@mui/material';
  import { AppLayout } from './components/Layout/AppLayout';
  import { theme } from './theme';
  ```

- [ ] Test all components:
  - Theme switching works
  - All panels display correctly
  - Audio visualizer animates
  - Real-time updates work
  - Responsive on different screen sizes

- [ ] Performance optimization:
  - Lazy load heavy components
  - Memoize expensive calculations
  - Debounce rapid updates
  - Optimize re-renders

### Phase 12: Documentation & Commit (15 min)

- [ ] Create component documentation:
  - Document props for each component
  - Add usage examples
  - Explain theme customization

- [ ] Update README with frontend section:
  - How to run dev server
  - How to build for production
  - Component structure
  - Customization guide

- [ ] Commit all changes:
  ```bash
  git add -A
  git commit -m "feat: Implement beautiful MUI-based frontend

  - Add Material-UI v5 with dark/light theme system
  - Create responsive AppLayout with 2x2 grid
  - Build real-time AudioVisualizer with waveform display
  - Enhance TranscriptionPanel with word highlighting
  - Improve InsightsPanel with MUI Chips and visual indicators
  - Update SummaryPanel with formatted display
  - Add MetricsDashboard with latency charts
  - Implement smooth animations and transitions
  - Add accessibility features and keyboard navigation

  The frontend now provides a professional, minimal, and stylish
  interface for real-time speech-to-text with full pipeline visibility.

  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

---

## Files to Create

### New Components:
```
src/ui/desktop/renderer/
├── theme.ts
├── contexts/
│   └── ThemeContext.tsx
├── components/
│   ├── Layout/
│   │   ├── AppLayout.tsx
│   │   ├── AppBar.tsx
│   │   └── StatusBar.tsx
│   ├── AudioVisualizer/
│   │   ├── AudioVisualizer.tsx
│   │   ├── Waveform.tsx
│   │   └── VUMeter.tsx
│   └── MetricsDashboard/
│       ├── MetricsDashboard.tsx
│       ├── LatencyChart.tsx
│       └── QualityGauge.tsx
└── hooks/
    └── useAudioVisualization.ts
```

### Files to Modify:
```
src/ui/desktop/renderer/
├── App.tsx (integrate new layout)
├── package.json (add MUI dependencies)
├── components/
│   ├── TranscriptionPanel.tsx (enhance with MUI)
│   ├── InsightsPanel.tsx (enhance with MUI)
│   └── SummaryPanel.tsx (enhance with MUI)
└── README.md (add frontend documentation)
```

---

## MUI Components to Use

### Layout:
- `AppBar` - Top application bar
- `Drawer` - Side navigation (optional)
- `Container` - Main content wrapper
- `Grid` - Responsive layout
- `Box` - Flexible container

### Display:
- `Card` - Panel containers
- `Paper` - Elevated surfaces
- `Typography` - Text styles
- `Chip` - Keywords/tags
- `Badge` - Notifications
- `Avatar` - User/speaker icons

### Inputs:
- `Button` - Actions
- `Fab` - Floating action button (recording)
- `IconButton` - Icon actions
- `Switch` - Toggle options
- `Select` - Dropdowns
- `Slider` - Volume control

### Feedback:
- `Skeleton` - Loading states
- `CircularProgress` - Loading spinner
- `LinearProgress` - Progress bar
- `Snackbar` - Notifications
- `Alert` - Status messages

### Navigation:
- `Tabs` - Section switching
- `BottomNavigation` - Mobile nav
- `Breadcrumbs` - Page hierarchy

---

## Color Palette (Dark Theme)

```typescript
const darkTheme = {
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',  // Blue
    },
    secondary: {
      main: '#f48fb1',  // Pink
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    success: {
      main: '#66bb6a',  // Green (audio levels good)
    },
    warning: {
      main: '#ffa726',  // Orange (audio levels high)
    },
    error: {
      main: '#f44336',  // Red (audio levels too high)
    },
  },
};
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Initial Load | < 2s |
| Component Render | < 16ms (60fps) |
| Audio Viz Update | < 33ms (30fps) |
| Transcription Update | < 100ms |
| Bundle Size | < 1MB (gzipped) |

---

## Testing Checklist

- [ ] MUI dependencies installed successfully
- [ ] Theme switching works (dark ↔ light)
- [ ] Layout responsive on all screen sizes
- [ ] Audio visualizer displays waveform
- [ ] Real-time transcription updates smoothly
- [ ] Insights panel shows keywords/entities
- [ ] Summary panel formats correctly
- [ ] Metrics dashboard shows live data
- [ ] All animations smooth (60fps)
- [ ] Keyboard navigation works
- [ ] Accessibility features functional
- [ ] No console errors or warnings

---

## Completion Criteria

✅ MUI v5 fully integrated
✅ Dark/light theme system working
✅ Responsive AppLayout implemented
✅ Real-time AudioVisualizer built
✅ All panels enhanced with MUI
✅ MetricsDashboard displays live data
✅ Smooth animations and transitions
✅ Accessible and keyboard-friendly
✅ Documentation complete
✅ Changes committed to branch

---

**Next Steps After Completion:**
1. Wait for other terminals to complete
2. Participate in Wave 2 Sync Agent
3. Merge to develop after sync validation
4. Test full stack with real audio input
5. Take screenshots for documentation
