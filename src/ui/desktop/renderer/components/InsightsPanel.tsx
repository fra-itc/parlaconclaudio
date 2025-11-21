import React, { useState, useEffect } from 'react';
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

      // Remove animation class after animation completes
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

  const getTypeConfig = (
    type: Insight['type']
  ): { color: string; backgroundColor: string; label: string; icon: string } => {
    switch (type) {
      case 'keyword':
        return {
          color: '#2196f3',
          backgroundColor: 'rgba(33, 150, 243, 0.15)',
          label: 'Keyword',
          icon: '&#128273;',
        };
      case 'entity':
        return {
          color: '#4caf50',
          backgroundColor: 'rgba(76, 175, 80, 0.15)',
          label: 'Entity',
          icon: '&#127919;',
        };
      case 'sentiment':
        return {
          color: '#ff9800',
          backgroundColor: 'rgba(255, 152, 0, 0.15)',
          label: 'Sentiment',
          icon: '&#128522;',
        };
      case 'topic':
        return {
          color: '#9c27b0',
          backgroundColor: 'rgba(156, 39, 176, 0.15)',
          label: 'Topic',
          icon: '&#128161;',
        };
      default:
        return {
          color: '#858585',
          backgroundColor: 'rgba(133, 133, 133, 0.15)',
          label: 'Unknown',
          icon: '&#128712;',
        };
    }
  };

  const getSentimentColor = (metadata?: Record<string, any>): string => {
    if (!metadata || !metadata.sentiment) return '#ff9800';

    const sentiment = metadata.sentiment.toLowerCase();
    if (sentiment === 'positive') return '#4caf50';
    if (sentiment === 'negative') return '#f44336';
    return '#ff9800'; // neutral
  };

  const filteredInsights =
    filter === 'all' ? insights : insights.filter((insight) => insight.type === filter);

  const filterTypes: Array<Insight['type'] | 'all'> = ['all', 'keyword', 'entity', 'sentiment', 'topic'];

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
      marginBottom: '12px',
    },
    titleIcon: {
      fontSize: '20px',
    },
    filterContainer: {
      display: 'flex',
      gap: '8px',
      flexWrap: 'wrap' as const,
    },
    filterButton: {
      padding: '6px 12px',
      fontSize: '11px',
      fontWeight: 500,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
      border: '1px solid #3e3e42',
      borderRadius: '4px',
      backgroundColor: '#1e1e1e',
      color: '#858585',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
    },
    filterButtonActive: {
      backgroundColor: '#2196f3',
      color: '#ffffff',
      borderColor: '#2196f3',
    },
    content: {
      flex: 1,
      overflowY: 'auto' as const,
      padding: '12px 0',
    },
    insightCard: {
      padding: '16px 20px',
      borderBottom: '1px solid #3e3e42',
      transition: 'all 0.3s ease',
      animation: 'fadeIn 0.5s ease',
    },
    insightCardHover: {
      backgroundColor: '#2d2d30',
    },
    insightHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '10px',
    },
    typeBadge: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
      fontSize: '11px',
      fontWeight: 600,
      padding: '4px 10px',
      borderRadius: '4px',
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
    },
    badgeIcon: {
      fontSize: '14px',
    },
    timestamp: {
      fontSize: '11px',
      color: '#858585',
      fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
    },
    insightContent: {
      fontSize: '14px',
      lineHeight: '1.6',
      color: '#e0e0e0',
      marginBottom: '8px',
    },
    metadata: {
      display: 'flex',
      flexWrap: 'wrap' as const,
      gap: '8px',
      marginTop: '8px',
    },
    metadataItem: {
      fontSize: '11px',
      padding: '3px 8px',
      backgroundColor: '#1e1e1e',
      border: '1px solid #3e3e42',
      borderRadius: '3px',
      color: '#858585',
    },
    metadataLabel: {
      fontWeight: 600,
      marginRight: '4px',
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
    badge: {
      display: 'inline-block',
      padding: '2px 6px',
      marginLeft: '8px',
      fontSize: '10px',
      fontWeight: 600,
      backgroundColor: '#3e3e42',
      color: '#e0e0e0',
      borderRadius: '10px',
    },
  };

  const [hoveredInsightId, setHoveredInsightId] = useState<string | null>(null);

  return (
    <div style={styles.container} role="region" aria-label="Insights Panel">
      <header style={styles.header}>
        <h2 style={styles.title}>
          <span style={styles.titleIcon}>&#128161;</span>
          Insights
          <span style={styles.badge}>{insights.length}</span>
        </h2>

        {/* Filter Buttons */}
        <div style={styles.filterContainer} role="group" aria-label="Filter insights by type">
          {filterTypes.map((type) => (
            <button
              key={type}
              style={{
                ...styles.filterButton,
                ...(filter === type ? styles.filterButtonActive : {}),
              }}
              onClick={() => setFilter(type)}
              aria-pressed={filter === type}
              aria-label={`Filter by ${type}`}
            >
              {type === 'all' ? 'All' : getTypeConfig(type as Insight['type']).label}
            </button>
          ))}
        </div>
      </header>

      <div style={styles.content} role="list" aria-label="Insights list">
        {filteredInsights.length === 0 ? (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>&#128373;</div>
            <h3 style={styles.emptyTitle}>
              {insights.length === 0 ? 'No Insights Yet' : `No ${filter} Insights`}
            </h3>
            <p style={styles.emptyDescription}>
              {insights.length === 0
                ? 'Insights will be generated automatically as transcription progresses.'
                : `Try selecting a different filter to see other types of insights.`}
            </p>
          </div>
        ) : (
          filteredInsights.map((insight: Insight) => {
            const typeConfig = getTypeConfig(insight.type);
            const isAnimating = animatingIds.has(insight.id);
            const isSentiment = insight.type === 'sentiment';
            const sentimentColor = isSentiment
              ? getSentimentColor(insight.metadata)
              : typeConfig.color;

            return (
              <div
                key={insight.id}
                style={{
                  ...styles.insightCard,
                  ...(hoveredInsightId === insight.id ? styles.insightCardHover : {}),
                  ...(isAnimating ? { animation: 'fadeIn 0.5s ease' } : {}),
                }}
                onMouseEnter={() => setHoveredInsightId(insight.id)}
                onMouseLeave={() => setHoveredInsightId(null)}
                role="listitem"
                aria-label={`${typeConfig.label} insight: ${insight.content}`}
              >
                <div style={styles.insightHeader}>
                  <span
                    style={{
                      ...styles.typeBadge,
                      color: isSentiment ? sentimentColor : typeConfig.color,
                      backgroundColor: isSentiment
                        ? `${sentimentColor}15`
                        : typeConfig.backgroundColor,
                    }}
                  >
                    <span
                      style={styles.badgeIcon}
                      dangerouslySetInnerHTML={{ __html: typeConfig.icon }}
                    ></span>
                    {typeConfig.label}
                  </span>
                  <time
                    style={styles.timestamp}
                    dateTime={new Date(insight.timestamp).toISOString()}
                  >
                    {formatTimestamp(insight.timestamp)}
                  </time>
                </div>

                <div style={styles.insightContent}>{insight.content}</div>

                {/* Metadata Display */}
                {insight.metadata && Object.keys(insight.metadata).length > 0 && (
                  <div style={styles.metadata}>
                    {Object.entries(insight.metadata).map(([key, value]) => (
                      <span key={key} style={styles.metadataItem}>
                        <span style={styles.metadataLabel}>{key}:</span>
                        {String(value)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      <style>
        {`
          @keyframes fadeIn {
            from {
              opacity: 0;
              transform: translateY(-10px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }

          /* Custom scrollbar styling */
          [role="region"] [role="list"]::-webkit-scrollbar {
            width: 8px;
          }

          [role="region"] [role="list"]::-webkit-scrollbar-track {
            background: #1e1e1e;
          }

          [role="region"] [role="list"]::-webkit-scrollbar-thumb {
            background: #3e3e42;
            border-radius: 4px;
          }

          [role="region"] [role="list"]::-webkit-scrollbar-thumb:hover {
            background: #4e4e52;
          }

          /* Filter button hover effect */
          button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
          }

          button:active {
            transform: translateY(0);
          }
        `}
      </style>
    </div>
  );
};

export default InsightsPanel;
