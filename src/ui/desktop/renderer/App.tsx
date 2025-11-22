import React, { useState } from 'react';
import TranscriptionPanel from './components/TranscriptionPanel';
import InsightsPanel from './components/InsightsPanel';
import SummaryPanel from './components/SummaryPanel';
import SettingsPanel from './components/SettingsPanel';
import TestPanelsWithMockData from './components/TestPanelsWithMockData';

type View = 'live' | 'demo' | 'settings';

const App: React.FC = () => {
  const [view, setView] = useState<View>('demo');

  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column' as const,
      height: '100vh',
      width: '100vw',
      backgroundColor: '#1e1e1e',
      color: '#e0e0e0',
      overflow: 'hidden',
    },
    header: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '12px 20px',
      backgroundColor: '#252526',
      borderBottom: '1px solid #3e3e42',
      minHeight: '50px',
    },
    title: {
      margin: 0,
      fontSize: '18px',
      fontWeight: 600,
      color: '#ffffff',
    },
    version: {
      fontSize: '12px',
      color: '#858585',
    },
    nav: {
      display: 'flex',
      gap: '8px',
    },
    navButton: (active: boolean) => ({
      padding: '8px 16px',
      backgroundColor: active ? '#0e639c' : '#3e3e42',
      color: active ? '#ffffff' : '#cccccc',
      border: 'none',
      borderRadius: '4px',
      cursor: 'pointer',
      fontSize: '13px',
      fontWeight: 500,
      transition: 'all 0.2s',
    }),
    main: {
      display: 'flex',
      flex: 1,
      overflow: 'hidden',
    },
    contentArea: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column' as const,
      overflow: 'hidden',
    },
    liveLayout: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gridTemplateRows: '1fr 1fr',
      gap: '16px',
      padding: '16px',
      height: '100%',
      overflow: 'hidden',
    },
    panelContainer: {
      backgroundColor: '#252526',
      borderRadius: '8px',
      border: '1px solid #3e3e42',
      overflow: 'hidden',
    },
    footer: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '8px 20px',
      backgroundColor: '#252526',
      borderTop: '1px solid #3e3e42',
      minHeight: '32px',
      fontSize: '12px',
      color: '#858585',
    },
    statusItem: {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
    },
    statusDot: (connected: boolean) => ({
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      backgroundColor: connected ? '#4caf50' : '#858585',
    }),
  };

  const renderContent = () => {
    switch (view) {
      case 'demo':
        return <TestPanelsWithMockData />;

      case 'live':
        return (
          <div style={styles.liveLayout}>
            <div style={styles.panelContainer}>
              <TranscriptionPanel />
            </div>
            <div style={styles.panelContainer}>
              <InsightsPanel />
            </div>
            <div style={styles.panelContainer}>
              <SummaryPanel />
            </div>
            <div style={styles.panelContainer}>
              <SettingsPanel />
            </div>
          </div>
        );

      case 'settings':
        return (
          <div style={{ padding: '16px', height: '100%' }}>
            <SettingsPanel />
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div>
          <h1 style={styles.title}>ORCHIDEA RTSTT</h1>
        </div>

        <nav style={styles.nav}>
          <button
            style={styles.navButton(view === 'demo')}
            onClick={() => setView('demo')}
            onMouseOver={(e) => {
              if (view !== 'demo') {
                e.currentTarget.style.backgroundColor = '#4e4e52';
              }
            }}
            onMouseOut={(e) => {
              if (view !== 'demo') {
                e.currentTarget.style.backgroundColor = '#3e3e42';
              }
            }}
          >
            Demo
          </button>
          <button
            style={styles.navButton(view === 'live')}
            onClick={() => setView('live')}
            onMouseOver={(e) => {
              if (view !== 'live') {
                e.currentTarget.style.backgroundColor = '#4e4e52';
              }
            }}
            onMouseOut={(e) => {
              if (view !== 'live') {
                e.currentTarget.style.backgroundColor = '#3e3e42';
              }
            }}
          >
            Live
          </button>
          <button
            style={styles.navButton(view === 'settings')}
            onClick={() => setView('settings')}
            onMouseOver={(e) => {
              if (view !== 'settings') {
                e.currentTarget.style.backgroundColor = '#4e4e52';
              }
            }}
            onMouseOut={(e) => {
              if (view !== 'settings') {
                e.currentTarget.style.backgroundColor = '#3e3e42';
              }
            }}
          >
            Settings
          </button>
        </nav>

        <span style={styles.version}>v1.0.0-POC</span>
      </header>

      {/* Main Content Area */}
      <main style={styles.main}>
        <div style={styles.contentArea}>
          {renderContent()}
        </div>
      </main>

      {/* Footer */}
      <footer style={styles.footer}>
        <div style={styles.statusItem}>
          <div style={styles.statusDot(view === 'demo')}></div>
          <span>{view === 'demo' ? 'Demo Mode' : view === 'live' ? 'Live Mode' : 'Settings'}</span>
        </div>
        <div>
          <span>Electron + React + Vite | ORCHIDEA Framework v1.3</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
