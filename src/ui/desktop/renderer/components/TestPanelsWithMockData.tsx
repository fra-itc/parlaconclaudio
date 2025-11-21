import React, { useEffect } from 'react';
import { useStore } from '../store';
import TranscriptionPanel from './TranscriptionPanel';
import InsightsPanel from './InsightsPanel';

/**
 * TEST COMPONENT WITH MOCK DATA
 *
 * This component demonstrates the TranscriptionPanel and InsightsPanel
 * with simulated real-time data updates.
 *
 * To test, simply import and render this component instead of the regular App.
 */

const TestPanelsWithMockData: React.FC = () => {
  const addTranscriptionSegment = useStore((state) => state.addTranscriptionSegment);
  const updateCurrentTranscription = useStore((state) => state.updateCurrentTranscription);
  const addInsight = useStore((state) => state.addInsight);
  const clearAll = useStore((state) => state.clearAll);

  useEffect(() => {
    // Clear all data on mount
    clearAll();

    // Simulate real-time transcription updates
    const mockTranscriptions = [
      'Hello, welcome to the ORCHIDEA real-time speech transcription system.',
      'This is a demonstration of how the transcription panel works.',
      'As you can see, each segment is displayed with a timestamp and confidence level.',
      'The system can also detect different speakers if that information is available.',
      'Insights are generated automatically from the transcribed text.',
    ];

    const mockInsightsData = [
      {
        type: 'keyword' as const,
        content: 'ORCHIDEA',
        metadata: { frequency: 3, relevance: 0.95 },
      },
      {
        type: 'entity' as const,
        content: 'real-time speech transcription system',
        metadata: { category: 'product', confidence: 0.92 },
      },
      {
        type: 'sentiment' as const,
        content: 'Positive sentiment detected in recent dialogue',
        metadata: { sentiment: 'positive', score: 0.87 },
      },
      {
        type: 'topic' as const,
        content: 'Technology and Innovation',
        metadata: { category: 'technology', relevance: 0.89 },
      },
      {
        type: 'keyword' as const,
        content: 'transcription',
        metadata: { frequency: 5, relevance: 0.91 },
      },
      {
        type: 'entity' as const,
        content: 'demonstration',
        metadata: { category: 'event', confidence: 0.85 },
      },
      {
        type: 'sentiment' as const,
        content: 'Neutral sentiment with informative tone',
        metadata: { sentiment: 'neutral', score: 0.65 },
      },
    ];

    let transcriptionIndex = 0;
    let insightIndex = 0;
    let isSimulating = true;

    // Simulate typing current transcription
    const simulateTyping = (text: string) => {
      let charIndex = 0;
      const typingInterval = setInterval(() => {
        if (!isSimulating) {
          clearInterval(typingInterval);
          return;
        }

        if (charIndex < text.length) {
          updateCurrentTranscription(text.substring(0, charIndex + 1));
          charIndex++;
        } else {
          clearInterval(typingInterval);
          // Finalize the segment after typing is complete
          setTimeout(() => {
            if (!isSimulating) return;

            addTranscriptionSegment({
              id: `segment-${Date.now()}-${transcriptionIndex}`,
              text: text,
              timestamp: Date.now(),
              speaker: transcriptionIndex % 3 === 0 ? 'Speaker A' : transcriptionIndex % 3 === 1 ? 'Speaker B' : undefined,
              confidence: 0.85 + Math.random() * 0.14, // Random confidence between 0.85 and 0.99
            });

            transcriptionIndex++;

            // Add insight occasionally
            if (insightIndex < mockInsightsData.length && Math.random() > 0.5) {
              const insightData = mockInsightsData[insightIndex];
              setTimeout(() => {
                if (!isSimulating) return;

                addInsight({
                  id: `insight-${Date.now()}-${insightIndex}`,
                  type: insightData.type,
                  content: insightData.content,
                  timestamp: Date.now(),
                  metadata: insightData.metadata,
                });
                insightIndex++;
              }, 500);
            }

            // Continue with next transcription
            if (transcriptionIndex < mockTranscriptions.length) {
              setTimeout(() => {
                if (!isSimulating) return;
                simulateTyping(mockTranscriptions[transcriptionIndex]);
              }, 1500);
            } else {
              // Loop back to start after a delay
              setTimeout(() => {
                if (!isSimulating) return;
                clearAll();
                transcriptionIndex = 0;
                insightIndex = 0;
                simulateTyping(mockTranscriptions[0]);
              }, 5000);
            }
          }, 1000);
        }
      }, 50); // Typing speed: 50ms per character
    };

    // Start simulation
    setTimeout(() => {
      simulateTyping(mockTranscriptions[0]);
    }, 1000);

    // Cleanup on unmount
    return () => {
      isSimulating = false;
      clearAll();
    };
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
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    title: {
      margin: 0,
      fontSize: '18px',
      fontWeight: 600,
      color: '#ffffff',
    },
    badge: {
      padding: '6px 12px',
      fontSize: '11px',
      fontWeight: 600,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
      backgroundColor: '#4caf50',
      color: '#ffffff',
      borderRadius: '4px',
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
      minWidth: 0,
    },
    footer: {
      padding: '12px 20px',
      backgroundColor: '#252526',
      borderTop: '1px solid #3e3e42',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      gap: '8px',
      fontSize: '12px',
      color: '#858585',
    },
    footerIcon: {
      fontSize: '16px',
    },
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>ORCHIDEA RTSTT - Test Mode</h1>
        <span style={styles.badge}>Simulating Live Data</span>
      </header>

      <main style={styles.main}>
        <div style={styles.panelContainer}>
          <TranscriptionPanel />
        </div>

        <div style={styles.panelContainer}>
          <InsightsPanel />
        </div>
      </main>

      <footer style={styles.footer}>
        <span style={styles.footerIcon}>&#128268;</span>
        <span>Mock data simulation active - panels update in real-time</span>
      </footer>
    </div>
  );
};

export default TestPanelsWithMockData;
