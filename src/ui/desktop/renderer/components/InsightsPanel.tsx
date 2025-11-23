import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Box,
  Typography,
  Chip,
  Button,
  ButtonGroup,
  Fade,
  Badge,
} from '@mui/material';
import {
  Lightbulb as LightbulbIcon,
  Label as LabelIcon,
  Business as BusinessIcon,
  SentimentSatisfied as SentimentIcon,
  Topic as TopicIcon,
} from '@mui/icons-material';
import { useInsights } from '../store';
import type { Insight } from '../store';

const InsightsPanel: React.FC = () => {
  const insights = useInsights();
  const [filter, setFilter] = useState<Insight['type'] | 'all'>('all');
  const [animatingIds, setAnimatingIds] = useState<Set<string>>(new Set());

  // Trigger fade-in animation for new insights
  useEffect(() => {
    if (insights.length > 0) {
      const latestInsight = insights[insights.length - 1];
      setAnimatingIds((prev) => new Set(prev).add(latestInsight.id));

      const timer = setTimeout(() => {
        setAnimatingIds((prev) => {
          const next = new Set(prev);
          next.delete(latestInsight.id);
          return next;
        });
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [insights.length]);

  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  const getTypeConfig = (type: Insight['type']) => {
    switch (type) {
      case 'keyword':
        return {
          color: 'primary' as const,
          label: 'Keyword',
          icon: <LabelIcon />,
        };
      case 'entity':
        return {
          color: 'success' as const,
          label: 'Entity',
          icon: <BusinessIcon />,
        };
      case 'sentiment':
        return {
          color: 'warning' as const,
          label: 'Sentiment',
          icon: <SentimentIcon />,
        };
      case 'topic':
        return {
          color: 'secondary' as const,
          label: 'Topic',
          icon: <TopicIcon />,
        };
      default:
        return {
          color: 'default' as const,
          label: 'Unknown',
          icon: <LabelIcon />,
        };
    }
  };

  const getSentimentColor = (metadata?: Record<string, any>): 'success' | 'warning' | 'error' => {
    if (!metadata || !metadata.sentiment) return 'warning';

    const sentiment = metadata.sentiment.toLowerCase();
    if (sentiment === 'positive') return 'success';
    if (sentiment === 'negative') return 'error';
    return 'warning'; // neutral
  };

  const filteredInsights =
    filter === 'all' ? insights : insights.filter((insight) => insight.type === filter);

  const filterTypes: Array<Insight['type'] | 'all'> = ['all', 'keyword', 'entity', 'sentiment', 'topic'];

  const getFilterCount = (type: Insight['type'] | 'all') => {
    if (type === 'all') return insights.length;
    return insights.filter((i) => i.type === type).length;
  };

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
        avatar={<LightbulbIcon color="primary" />}
        title={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            Insights
            <Chip label={insights.length} size="small" color="primary" />
          </Box>
        }
        titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
        subheader={
          <Box sx={{ mt: 1.5 }}>
            <ButtonGroup size="small" variant="outlined" fullWidth>
              {filterTypes.map((type) => {
                const config = type !== 'all' ? getTypeConfig(type as Insight['type']) : null;
                const count = getFilterCount(type);

                return (
                  <Button
                    key={type}
                    onClick={() => setFilter(type)}
                    variant={filter === type ? 'contained' : 'outlined'}
                    sx={{
                      textTransform: 'uppercase',
                      fontSize: '0.7rem',
                      fontWeight: 600,
                    }}
                  >
                    <Badge badgeContent={count} color="primary" max={99}>
                      {type === 'all' ? 'All' : config?.label}
                    </Badge>
                  </Button>
                );
              })}
            </ButtonGroup>
          </Box>
        }
        sx={{ pb: 1 }}
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
        {filteredInsights.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              p: 5,
              textAlign: 'center',
              minHeight: 200,
            }}
          >
            <LightbulbIcon sx={{ fontSize: 64, opacity: 0.3, mb: 2 }} />
            <Typography variant="h6" fontWeight={600} gutterBottom>
              {insights.length === 0 ? 'No Insights Yet' : `No ${filter} Insights`}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 300 }}>
              {insights.length === 0
                ? 'Insights will be generated automatically as transcription progresses.'
                : 'Try selecting a different filter to see other types of insights.'}
            </Typography>
          </Box>
        ) : (
          filteredInsights.map((insight: Insight) => {
            const typeConfig = getTypeConfig(insight.type);
            const isAnimating = animatingIds.has(insight.id);
            const isSentiment = insight.type === 'sentiment';
            const sentimentColor = isSentiment ? getSentimentColor(insight.metadata) : typeConfig.color;

            return (
              <Fade in key={insight.id}>
                <Box
                  sx={{
                    p: 2.5,
                    borderBottom: 1,
                    borderColor: 'divider',
                    transition: 'background-color 0.2s ease',
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
                      mb: 1.5,
                    }}
                  >
                    <Chip
                      icon={typeConfig.icon}
                      label={typeConfig.label}
                      size="small"
                      color={isSentiment ? sentimentColor : typeConfig.color}
                      sx={{ fontWeight: 600 }}
                    />
                    <Typography
                      variant="caption"
                      sx={{
                        fontFamily: 'monospace',
                        color: 'text.secondary',
                      }}
                    >
                      {formatTimestamp(insight.timestamp)}
                    </Typography>
                  </Box>

                  <Typography
                    variant="body2"
                    sx={{
                      mb: insight.metadata && Object.keys(insight.metadata).length > 0 ? 1 : 0,
                      lineHeight: 1.6,
                    }}
                  >
                    {insight.content}
                  </Typography>

                  {/* Metadata Display */}
                  {insight.metadata && Object.keys(insight.metadata).length > 0 && (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {Object.entries(insight.metadata).map(([key, value]) => (
                        <Chip
                          key={key}
                          label={`${key}: ${String(value)}`}
                          size="small"
                          variant="outlined"
                          sx={{
                            fontSize: '0.7rem',
                            height: 20,
                          }}
                        />
                      ))}
                    </Box>
                  )}
                </Box>
              </Fade>
            );
          })
        )}
      </CardContent>
    </Card>
  );
};

export default InsightsPanel;
