import React from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { AppLayout, GridLayout } from './components/Layout/AppLayout';
import { AudioVisualizer } from './components/AudioVisualizer/AudioVisualizer';
import TranscriptionPanel from './components/TranscriptionPanel';
import InsightsPanel from './components/InsightsPanel';
import { SummaryPanel } from './components/SummaryPanel';
import { MetricsDashboard } from './components/MetricsDashboard/MetricsDashboard';

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AppLayout>
        <GridLayout
          topLeft={<AudioVisualizer />}
          topRight={<TranscriptionPanel />}
          bottomLeft={<InsightsPanel />}
          bottomRight={<SummaryPanel />}
        />
      </AppLayout>
    </ThemeProvider>
  );
};

export default App;
