import React from 'react';

const App: React.FC = () => {
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
    main: {
      display: 'flex',
      flex: 1,
      overflow: 'hidden',
    },
    contentArea: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column' as const,
      padding: '20px',
      overflow: 'auto',
    },
    placeholder: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flex: 1,
      border: '2px dashed #3e3e42',
      borderRadius: '8px',
      padding: '40px',
      textAlign: 'center' as const,
    },
    placeholderText: {
      fontSize: '16px',
      color: '#858585',
      lineHeight: '1.6',
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
    statusDot: {
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      backgroundColor: '#4caf50',
    },
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <h1 style={styles.title}>ORCHIDEA RTSTT</h1>
        <span style={styles.version}>v0.1.0-alpha</span>
      </header>

      {/* Main Content Area */}
      <main style={styles.main}>
        <div style={styles.contentArea}>
          <div style={styles.placeholder}>
            <div>
              <h2 style={styles.placeholderText}>
                <strong>ORCHIDEA Real-Time STT</strong>
              </h2>
              <p style={styles.placeholderText}>
                React base setup complete.
                <br />
                UI panels and components will be added in the next steps.
              </p>
              <p style={styles.placeholderText}>
                <em>Audio Waveform | Controls | Transcription Display</em>
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer style={styles.footer}>
        <div style={styles.statusItem}>
          <div style={styles.statusDot}></div>
          <span>Ready</span>
        </div>
        <div>
          <span>Electron + React + Vite</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
