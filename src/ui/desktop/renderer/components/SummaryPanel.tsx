import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Box,
  Typography,
  IconButton,
  Chip,
  Collapse,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Tooltip,
  Fade,
  Divider,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  Refresh as RefreshIcon,
  ContentCopy as CopyIcon,
  Check as CheckIcon,
  History as HistoryIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useSummaries, useCurrentSummary, useStore } from '../store';

export const SummaryPanel: React.FC = () => {
  const summaries = useSummaries();
  const currentSummary = useCurrentSummary();
  const { setCurrentSummary } = useStore();
  const [showHistory, setShowHistory] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Format timestamp for display
  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // Copy to clipboard handler
  const copyToClipboard = async (content: string, id: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  // Placeholder for regenerate functionality
  const handleRegenerate = () => {
    console.log('Regenerate summary - to be implemented');
  };

  // Empty state
  if (summaries.length === 0) {
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
          avatar={<DescriptionIcon color="primary" />}
          title="Summary"
          titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
        />
        <CardContent
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
          <DescriptionIcon sx={{ fontSize: 64, opacity: 0.3, mb: 2 }} />
          <Typography variant="h6" fontWeight={600} gutterBottom>
            No Summaries Yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 300 }}>
            Summaries will appear here once they are generated from your transcriptions.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  // Get the latest summary if no current summary is selected
  const displaySummary = currentSummary || summaries[summaries.length - 1];

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
        avatar={<DescriptionIcon color="primary" />}
        title="Summary"
        titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
        action={
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <Tooltip title="Regenerate summary">
              <IconButton onClick={handleRegenerate} size="small">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            {summaries.length > 1 && (
              <Tooltip title={showHistory ? 'Hide history' : 'Show history'}>
                <IconButton
                  onClick={() => setShowHistory(!showHistory)}
                  size="small"
                  sx={{
                    transform: showHistory ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.3s',
                  }}
                >
                  <HistoryIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        }
      />

      <CardContent
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 0,
          '&:last-child': { pb: 0 },
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
        {/* Current/Latest Summary */}
        <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Typography variant="subtitle1" fontWeight={600} color="primary">
                  {currentSummary ? 'Current Summary' : 'Latest Summary'}
                </Typography>
                {displaySummary.id === summaries[summaries.length - 1].id && (
                  <Chip label="Latest" size="small" color="success" />
                )}
              </Box>
              <Typography variant="caption" color="text.secondary">
                Generated on {formatTimestamp(displaySummary.timestamp)}
              </Typography>
            </Box>
            <Tooltip title={copiedId === displaySummary.id ? 'Copied!' : 'Copy to clipboard'}>
              <IconButton
                size="small"
                onClick={() => copyToClipboard(displaySummary.content, displaySummary.id)}
                color={copiedId === displaySummary.id ? 'success' : 'default'}
              >
                {copiedId === displaySummary.id ? <CheckIcon /> : <CopyIcon />}
              </IconButton>
            </Tooltip>
          </Box>

          {/* Summary Content */}
          <Typography
            variant="body2"
            sx={{
              lineHeight: 1.7,
              whiteSpace: 'pre-wrap',
              color: 'text.primary',
            }}
          >
            {displaySummary.content}
          </Typography>

          {/* Key Points */}
          {displaySummary.keyPoints && displaySummary.keyPoints.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography
                variant="caption"
                sx={{
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: 0.5,
                  color: 'text.secondary',
                  mb: 1.5,
                  display: 'block',
                }}
              >
                Key Points
              </Typography>
              <List dense sx={{ pl: 0 }}>
                {displaySummary.keyPoints.map((point, index) => (
                  <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <CheckCircleIcon color="primary" sx={{ fontSize: 18 }} />
                    </ListItemIcon>
                    <ListItemText
                      primary={point}
                      primaryTypographyProps={{
                        variant: 'body2',
                        color: 'text.primary',
                      }}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </Box>

        {/* History Section */}
        <Collapse in={showHistory && summaries.length > 1}>
          <Box sx={{ p: 3 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Previous Summaries ({summaries.length - 1})
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 2 }}>
              {summaries
                .slice()
                .reverse()
                .slice(1) // Skip the first one (latest) as it's already displayed above
                .map((summary) => (
                  <Fade in key={summary.id}>
                    <Paper
                      elevation={currentSummary?.id === summary.id ? 3 : 1}
                      sx={{
                        p: 2,
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        border: 1,
                        borderColor: currentSummary?.id === summary.id ? 'primary.main' : 'divider',
                        bgcolor: currentSummary?.id === summary.id ? 'action.selected' : 'background.paper',
                        '&:hover': {
                          borderColor: 'primary.light',
                          elevation: 2,
                        },
                      }}
                      onClick={() => setCurrentSummary(summary)}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          {formatTimestamp(summary.timestamp)}
                        </Typography>
                        <Tooltip title={copiedId === summary.id ? 'Copied!' : 'Copy'}>
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              copyToClipboard(summary.content, summary.id);
                            }}
                            color={copiedId === summary.id ? 'success' : 'default'}
                          >
                            {copiedId === summary.id ? <CheckIcon fontSize="small" /> : <CopyIcon fontSize="small" />}
                          </IconButton>
                        </Tooltip>
                      </Box>
                      <Typography
                        variant="body2"
                        sx={{
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {summary.content}
                      </Typography>
                      {summary.keyPoints && summary.keyPoints.length > 0 && (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                          {summary.keyPoints.length} key point{summary.keyPoints.length !== 1 ? 's' : ''}
                        </Typography>
                      )}
                    </Paper>
                  </Fade>
                ))}
            </Box>
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default SummaryPanel;
