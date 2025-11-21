import React, { useEffect, useRef } from 'react';
import { useTranscription, useCurrentTranscription, useSettings } from '../store';
import type { TranscriptionSegment } from '../store';

const TranscriptionPanel: React.FC = () => {
  const transcription = useTranscription();
  const currentTranscription = useCurrentTranscription();
  const settings = useSettings();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new segments arrive
  useEffect(() => {
    if (settings.autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcription, currentTranscription, settings.autoScroll]);

  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  const getConfidenceColor = (confidence?: number): string => {
    if (!confidence) return '#858585';
    if (confidence >= 0.9) return '#4caf50';
    if (confidence >= 0.7) return '#ff9800';
    return '#f44336';
  };

  const getConfidenceLabel = (confidence?: number): string => {
    if (!confidence) return 'N/A';
    if (confidence >= 0.9) return 'High';
    if (confidence >= 0.7) return 'Medium';
    return 'Low';
  };

  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column' as const,
      height: '100%',
      backgroundColor: '#252526',
      border: '1px solid #3e3e42',
      borderRadius: '8px',
      overflow: 'hidden',
    },
    header: {
      padding: '16px 20px',
      backgroundColor: '#2d2d30',
      borderBottom: '1px solid #3e3e42',
    },
    title: {
      margin: 0,
      fontSize: '16px',
      fontWeight: 600,
      color: '#ffffff',
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
    },
    titleIcon: {
      fontSize: '20px',
    },
    content: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column' as const,
      overflow: 'hidden',
    },
    currentSection: {
      padding: '16px 20px',
      backgroundColor: '#1e1e1e',
      borderBottom: '1px solid #3e3e42',
      minHeight: '80px',
    },
    currentLabel: {
      fontSize: '11px',
      fontWeight: 600,
      color: '#858585',
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
      marginBottom: '8px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
    },
    speakingIndicator: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
    },
    speakingDot: {
      width: '6px',
      height: '6px',
      borderRadius: '50%',
      backgroundColor: '#4caf50',
      animation: 'pulse 1.5s ease-in-out infinite',
    },
    currentText: {
      fontSize: '14px',
      lineHeight: '1.6',
      color: '#e0e0e0',
      fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
      minHeight: '22px',
    },
    emptyCurrentText: {
      color: '#858585',
      fontStyle: 'italic' as const,
    },
    historySection: {
      flex: 1,
      overflowY: 'auto' as const,
      padding: '12px 0',
    },
    segment: {
      padding: '12px 20px',
      borderBottom: '1px solid #3e3e42',
      transition: 'background-color 0.2s ease',
    },
    segmentHover: {
      backgroundColor: '#2d2d30',
    },
    segmentHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '8px',
    },
    segmentMeta: {
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
    },
    timestamp: {
      fontSize: '11px',
      color: '#858585',
      fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
    },
    speaker: {
      fontSize: '11px',
      fontWeight: 600,
      color: '#4fc3f7',
      padding: '2px 8px',
      backgroundColor: 'rgba(79, 195, 247, 0.15)',
      borderRadius: '4px',
    },
    confidence: {
      fontSize: '11px',
      fontWeight: 500,
      padding: '2px 8px',
      borderRadius: '4px',
      display: 'inline-flex',
      alignItems: 'center',
      gap: '4px',
    },
    confidenceDot: {
      width: '6px',
      height: '6px',
      borderRadius: '50%',
    },
    segmentText: {
      fontSize: '14px',
      lineHeight: '1.6',
      color: '#e0e0e0',
      fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
    },
    emptyState: {
      display: 'flex',
      flexDirection: 'column' as const,
      alignItems: 'center',
      justifyContent: 'center',
      height: '100%',
      padding: '40px 20px',
      textAlign: 'center' as const,
    },
    emptyIcon: {
      fontSize: '48px',
      marginBottom: '16px',
      opacity: 0.3,
    },
    emptyTitle: {
      fontSize: '16px',
      fontWeight: 600,
      color: '#ffffff',
      marginBottom: '8px',
    },
    emptyDescription: {
      fontSize: '13px',
      color: '#858585',
      lineHeight: '1.6',
      maxWidth: '300px',
    },
  };

  const [hoveredSegmentId, setHoveredSegmentId] = React.useState<string | null>(null);

  const isEmpty = transcription.length === 0 && !currentTranscription;

  return (
    <div style={styles.container} role="region" aria-label="Transcription Panel">
      <header style={styles.header}>
        <h2 style={styles.title}>
          <span style={styles.titleIcon}>&#128172;</span>
          Transcription
        </h2>
      </header>

      <div style={styles.content}>
        {/* Current Transcription (Real-time) */}
        <section style={styles.currentSection} aria-label="Current transcription">
          <div style={styles.currentLabel}>
            {currentTranscription && (
              <span style={styles.speakingIndicator}>
                <span style={styles.speakingDot}></span>
                Speaking...
              </span>
            )}
            {!currentTranscription && 'Current'}
          </div>
          <div
            style={{
              ...styles.currentText,
              ...(currentTranscription ? {} : styles.emptyCurrentText),
            }}
          >
            {currentTranscription || 'Waiting for speech...'}
          </div>
        </section>

        {/* Finalized Segments (History) */}
        {isEmpty ? (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>&#128363;</div>
            <h3 style={styles.emptyTitle}>No Transcriptions Yet</h3>
            <p style={styles.emptyDescription}>
              Start speaking or connect to the WebSocket to see real-time transcriptions appear
              here.
            </p>
          </div>
        ) : (
          <section
            ref={scrollRef}
            style={styles.historySection}
            aria-label="Transcription history"
          >
            {transcription.map((segment: TranscriptionSegment) => (
              <div
                key={segment.id}
                style={{
                  ...styles.segment,
                  ...(hoveredSegmentId === segment.id ? styles.segmentHover : {}),
                }}
                onMouseEnter={() => setHoveredSegmentId(segment.id)}
                onMouseLeave={() => setHoveredSegmentId(null)}
                role="article"
                aria-label={`Transcription segment from ${formatTimestamp(segment.timestamp)}`}
              >
                <div style={styles.segmentHeader}>
                  <div style={styles.segmentMeta}>
                    <time style={styles.timestamp} dateTime={new Date(segment.timestamp).toISOString()}>
                      {formatTimestamp(segment.timestamp)}
                    </time>
                    {segment.speaker && (
                      <span style={styles.speaker} aria-label={`Speaker: ${segment.speaker}`}>
                        {segment.speaker}
                      </span>
                    )}
                  </div>
                  {segment.confidence !== undefined && (
                    <span
                      style={{
                        ...styles.confidence,
                        color: getConfidenceColor(segment.confidence),
                        backgroundColor: `${getConfidenceColor(segment.confidence)}15`,
                      }}
                      aria-label={`Confidence: ${getConfidenceLabel(segment.confidence)}`}
                    >
                      <span
                        style={{
                          ...styles.confidenceDot,
                          backgroundColor: getConfidenceColor(segment.confidence),
                        }}
                      ></span>
                      {getConfidenceLabel(segment.confidence)}
                    </span>
                  )}
                </div>
                <p style={styles.segmentText}>{segment.text}</p>
              </div>
            ))}
          </section>
        )}
      </div>

      <style>
        {`
          @keyframes pulse {
            0%, 100% {
              opacity: 1;
              transform: scale(1);
            }
            50% {
              opacity: 0.5;
              transform: scale(1.2);
            }
          }

          /* Custom scrollbar styling */
          [role="region"] [aria-label="Transcription history"]::-webkit-scrollbar {
            width: 8px;
          }

          [role="region"] [aria-label="Transcription history"]::-webkit-scrollbar-track {
            background: #1e1e1e;
          }

          [role="region"] [aria-label="Transcription history"]::-webkit-scrollbar-thumb {
            background: #3e3e42;
            border-radius: 4px;
          }

          [role="region"] [aria-label="Transcription history"]::-webkit-scrollbar-thumb:hover {
            background: #4e4e52;
          }
        `}
      </style>
    </div>
  );
};

export default TranscriptionPanel;
