import React, { useEffect, useRef } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Box,
  Typography,
  Chip,
  Fade,
  Divider,
} from '@mui/material';
import {
  RecordVoiceOver as RecordVoiceOverIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
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

  const getConfidenceColor = (confidence?: number): 'success' | 'warning' | 'error' | 'default' => {
    if (!confidence) return 'default';
    if (confidence >= 0.9) return 'success';
    if (confidence >= 0.7) return 'warning';
    return 'error';
  };

  const getConfidenceLabel = (confidence?: number): string => {
    if (!confidence) return 'N/A';
    if (confidence >= 0.9) return 'High';
    if (confidence >= 0.7) return 'Medium';
    return 'Low';
  };

  const [hoveredSegmentId, setHoveredSegmentId] = React.useState<string | null>(null);
  const isEmpty = transcription.length === 0 && !currentTranscription;

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <CardHeader
        avatar={<RecordVoiceOverIcon color="primary" />}
        title="Transcription"
        titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
      />

      <CardContent
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          p: 0,
          '&:last-child': { pb: 0 },
        }}
      >
        {/* Current Transcription (Real-time) */}
        <Box
          sx={{
            p: 2.5,
            bgcolor: 'background.default',
            borderBottom: 1,
            borderColor: 'divider',
            minHeight: 100,
          }}
        >
          <Typography
            variant="caption"
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              mb: 1,
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              color: 'text.secondary',
            }}
          >
            {currentTranscription && (
              <Chip
                size="small"
                label="Speaking"
                color="success"
                sx={{
                  height: 20,
                  fontSize: '0.7rem',
                  animation: 'pulse 1.5s ease-in-out infinite',
                }}
              />
            )}
            {!currentTranscription && 'Current'}
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontFamily: 'monospace',
              color: currentTranscription ? 'text.primary' : 'text.disabled',
              fontStyle: currentTranscription ? 'normal' : 'italic',
              lineHeight: 1.6,
            }}
          >
            {currentTranscription || 'Waiting for speech...'}
          </Typography>
        </Box>

        {/* Finalized Segments (History) */}
        {isEmpty ? (
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              p: 5,
              textAlign: 'center',
            }}
          >
            <RecordVoiceOverIcon sx={{ fontSize: 64, opacity: 0.3, mb: 2 }} />
            <Typography variant="h6" fontWeight={600} gutterBottom>
              No Transcriptions Yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 300 }}>
              Start speaking or connect to the WebSocket to see real-time transcriptions appear here.
            </Typography>
          </Box>
        ) : (
          <Box
            ref={scrollRef}
            sx={{
              flex: 1,
              overflowY: 'auto',
              '&::-webkit-scrollbar': {
                width: 8,
              },
              '&::-webkit-scrollbar-track': {
                bgcolor: 'background.default',
              },
              '&::-webkit-scrollbar-thumb': {
                bgcolor: 'divider',
                borderRadius: 1,
                '&:hover': {
                  bgcolor: 'text.disabled',
                },
              },
            }}
          >
            {transcription.map((segment: TranscriptionSegment) => (
              <Fade in key={segment.id}>
                <Box
                  onMouseEnter={() => setHoveredSegmentId(segment.id)}
                  onMouseLeave={() => setHoveredSegmentId(null)}
                  sx={{
                    p: 2.5,
                    borderBottom: 1,
                    borderColor: 'divider',
                    transition: 'background-color 0.2s ease',
                    bgcolor: hoveredSegmentId === segment.id ? 'action.hover' : 'transparent',
                    '&:hover': {
                      bgcolor: 'action.hover',
                    },
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 1,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Typography
                        variant="caption"
                        sx={{
                          fontFamily: 'monospace',
                          color: 'text.secondary',
                        }}
                      >
                        {formatTimestamp(segment.timestamp)}
                      </Typography>
                      {segment.speaker && (
                        <Chip
                          icon={<PersonIcon />}
                          label={segment.speaker}
                          size="small"
                          color="info"
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                      )}
                    </Box>
                    {segment.confidence !== undefined && (
                      <Chip
                        label={getConfidenceLabel(segment.confidence)}
                        size="small"
                        color={getConfidenceColor(segment.confidence)}
                        sx={{ height: 20, fontSize: '0.7rem', fontWeight: 500 }}
                      />
                    )}
                  </Box>
                  <Typography
                    variant="body2"
                    sx={{
                      fontFamily: 'monospace',
                      lineHeight: 1.6,
                    }}
                  >
                    {segment.text}
                  </Typography>
                </Box>
              </Fade>
            ))}
          </Box>
        )}
      </CardContent>

      <style>
        {`
          @keyframes pulse {
            0%, 100% {
              opacity: 1;
            }
            50% {
              opacity: 0.6;
            }
          }
        `}
      </style>
    </Card>
  );
};

export default TranscriptionPanel;
