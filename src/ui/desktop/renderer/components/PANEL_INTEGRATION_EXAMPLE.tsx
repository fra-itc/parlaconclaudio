import React from 'react';
import TranscriptionPanel from './TranscriptionPanel';
import InsightsPanel from './InsightsPanel';

/**
 * PANEL INTEGRATION EXAMPLE
 *
 * This file demonstrates how to integrate TranscriptionPanel and InsightsPanel
 * into your main App.tsx or any parent component.
 *
 * Both panels automatically connect to the Zustand store and receive real-time
 * updates from the WebSocket connection.
 */

// ============================================================================
// EXAMPLE 1: Side-by-Side Layout (Recommended for wide screens)
// ============================================================================
export const SideBySideLayout: React.FC = () => {
  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column' as const,
      height: '100vh',
      backgroundColor: '#1e1e1e',
    },
    header: {
      padding: '16px 20px',
      backgroundColor: '#252526',
      borderBottom: '1px solid #3e3e42',
    },
    title: {
      margin: 0,
      fontSize: '18px',
      fontWeight: 600,
      color: '#ffffff',
    },
    main: {
      display: 'flex',
      flex: 1,
      gap: '16px',
      padding: '16px',
      overflow: 'hidden',
    },
    panelContainer: {
      flex: 1,
      minWidth: 0, // Important for flex children
    },
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>ORCHIDEA RTSTT - Side by Side</h1>
      </header>

      <main style={styles.main}>
        {/* Left panel: Transcription */}
        <div style={styles.panelContainer}>
          <TranscriptionPanel />
        </div>

        {/* Right panel: Insights */}
        <div style={styles.panelContainer}>
          <InsightsPanel />
        </div>
      </main>
    </div>
  );
};

// ============================================================================
// EXAMPLE 2: Stacked Layout (Good for narrow screens or vertical preference)
// ============================================================================
export const StackedLayout: React.FC = () => {
  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column' as const,
      height: '100vh',
      backgroundColor: '#1e1e1e',
    },
    header: {
      padding: '16px 20px',
      backgroundColor: '#252526',
      borderBottom: '1px solid #3e3e42',
    },
    title: {
      margin: 0,
      fontSize: '18px',
      fontWeight: 600,
      color: '#ffffff',
    },
    main: {
      display: 'flex',
      flexDirection: 'column' as const,
      flex: 1,
      gap: '16px',
      padding: '16px',
      overflow: 'hidden',
    },
    panelContainer: {
      flex: 1,
      minHeight: 0, // Important for flex children
    },
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>ORCHIDEA RTSTT - Stacked</h1>
      </header>

      <main style={styles.main}>
        {/* Top panel: Transcription */}
        <div style={styles.panelContainer}>
          <TranscriptionPanel />
        </div>

        {/* Bottom panel: Insights */}
        <div style={styles.panelContainer}>
          <InsightsPanel />
        </div>
      </main>
    </div>
  );
};

// ============================================================================
// EXAMPLE 3: Asymmetric Layout (70/30 split - More space for transcription)
// ============================================================================
export const AsymmetricLayout: React.FC = () => {
  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column' as const,
      height: '100vh',
      backgroundColor: '#1e1e1e',
    },
    header: {
      padding: '16px 20px',
      backgroundColor: '#252526',
      borderBottom: '1px solid #3e3e42',
    },
    title: {
      margin: 0,
      fontSize: '18px',
      fontWeight: 600,
      color: '#ffffff',
    },
    main: {
      display: 'flex',
      flex: 1,
      gap: '16px',
      padding: '16px',
      overflow: 'hidden',
    },
    transcriptionContainer: {
      flex: 7, // 70% width
      minWidth: 0,
    },
    insightsContainer: {
      flex: 3, // 30% width
      minWidth: 0,
    },
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>ORCHIDEA RTSTT - Asymmetric</h1>
      </header>

      <main style={styles.main}>
        {/* Large panel: Transcription (70%) */}
        <div style={styles.transcriptionContainer}>
          <TranscriptionPanel />
        </div>

        {/* Small panel: Insights (30%) */}
        <div style={styles.insightsContainer}>
          <InsightsPanel />
        </div>
      </main>
    </div>
  );
};

// ============================================================================
// EXAMPLE 4: Tabbed Layout (Switch between panels)
// ============================================================================
export const TabbedLayout: React.FC = () => {
  const [activeTab, setActiveTab] = React.useState<'transcription' | 'insights'>('transcription');

  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column' as const,
      height: '100vh',
      backgroundColor: '#1e1e1e',
    },
    header: {
      padding: '16px 20px',
      backgroundColor: '#252526',
      borderBottom: '1px solid #3e3e42',
    },
    title: {
      margin: 0,
      fontSize: '18px',
      fontWeight: 600,
      color: '#ffffff',
    },
    tabBar: {
      display: 'flex',
      gap: '2px',
      backgroundColor: '#252526',
      borderBottom: '1px solid #3e3e42',
      padding: '0 16px',
    },
    tab: {
      padding: '12px 24px',
      backgroundColor: '#1e1e1e',
      color: '#858585',
      border: 'none',
      borderBottom: '2px solid transparent',
      cursor: 'pointer',
      fontSize: '13px',
      fontWeight: 500,
      transition: 'all 0.2s ease',
    },
    activeTab: {
      color: '#ffffff',
      borderBottomColor: '#2196f3',
      backgroundColor: '#252526',
    },
    main: {
      flex: 1,
      padding: '16px',
      overflow: 'hidden',
    },
    panelContainer: {
      height: '100%',
    },
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>ORCHIDEA RTSTT - Tabbed</h1>
      </header>

      <div style={styles.tabBar}>
        <button
          style={{
            ...styles.tab,
            ...(activeTab === 'transcription' ? styles.activeTab : {}),
          }}
          onClick={() => setActiveTab('transcription')}
        >
          Transcription
        </button>
        <button
          style={{
            ...styles.tab,
            ...(activeTab === 'insights' ? styles.activeTab : {}),
          }}
          onClick={() => setActiveTab('insights')}
        >
          Insights
        </button>
      </div>

      <main style={styles.main}>
        <div style={styles.panelContainer}>
          {activeTab === 'transcription' ? <TranscriptionPanel /> : <InsightsPanel />}
        </div>
      </main>
    </div>
  );
};

// ============================================================================
// EXAMPLE 5: Responsive Layout (Auto-switch based on screen size)
// ============================================================================
export const ResponsiveLayout: React.FC = () => {
  const [isWideScreen, setIsWideScreen] = React.useState(window.innerWidth >= 1200);

  React.useEffect(() => {
    const handleResize = () => {
      setIsWideScreen(window.innerWidth >= 1200);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column' as const,
      height: '100vh',
      backgroundColor: '#1e1e1e',
    },
    header: {
      padding: '16px 20px',
      backgroundColor: '#252526',
      borderBottom: '1px solid #3e3e42',
    },
    title: {
      margin: 0,
      fontSize: '18px',
      fontWeight: 600,
      color: '#ffffff',
    },
    main: {
      display: 'flex',
      flexDirection: isWideScreen ? ('row' as const) : ('column' as const),
      flex: 1,
      gap: '16px',
      padding: '16px',
      overflow: 'hidden',
    },
    panelContainer: {
      flex: 1,
      minWidth: 0,
      minHeight: 0,
    },
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>
          ORCHIDEA RTSTT - Responsive {isWideScreen ? '(Wide)' : '(Narrow)'}
        </h1>
      </header>

      <main style={styles.main}>
        <div style={styles.panelContainer}>
          <TranscriptionPanel />
        </div>

        <div style={styles.panelContainer}>
          <InsightsPanel />
        </div>
      </main>
    </div>
  );
};

// ============================================================================
// HOW TO USE IN App.tsx
// ============================================================================

/**
 * To integrate into your existing App.tsx, simply import one of these layouts
 * or create your own custom layout:
 *
 * ```tsx
 * import React from 'react';
 * import { SideBySideLayout } from './components/PANEL_INTEGRATION_EXAMPLE';
 *
 * const App: React.FC = () => {
 *   return <SideBySideLayout />;
 * };
 *
 * export default App;
 * ```
 *
 * OR, import the panels directly:
 *
 * ```tsx
 * import React from 'react';
 * import TranscriptionPanel from './components/TranscriptionPanel';
 * import InsightsPanel from './components/InsightsPanel';
 *
 * const App: React.FC = () => {
 *   return (
 *     <div style={{ display: 'flex', gap: '16px', padding: '16px', height: '100vh' }}>
 *       <div style={{ flex: 1 }}>
 *         <TranscriptionPanel />
 *       </div>
 *       <div style={{ flex: 1 }}>
 *         <InsightsPanel />
 *       </div>
 *     </div>
 *   );
 * };
 *
 * export default App;
 * ```
 */

// Export default layout for quick usage
export default SideBySideLayout;
