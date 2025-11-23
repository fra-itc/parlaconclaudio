import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Box,
  Typography,
  Grid,
  Paper,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
  Memory as MemoryIcon,
  Cloud as CloudIcon,
} from '@mui/icons-material';
import { useStore } from '../../store';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  color: 'primary' | 'success' | 'warning' | 'error' | 'info';
  icon: React.ReactNode;
  progress?: number;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, unit, color, icon, progress }) => {
  return (
    <Paper
      elevation={2}
      sx={{
        p: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.3s ease',
        '&:hover': {
          elevation: 4,
          transform: 'translateY(-2px)',
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>
          {title}
        </Typography>
        <Box sx={{ color: `${color}.main` }}>{icon}</Box>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5, mb: progress !== undefined ? 1 : 0 }}>
        <Typography variant="h4" fontWeight={700} color={`${color}.main`}>
          {value}
        </Typography>
        {unit && (
          <Typography variant="body2" color="text.secondary">
            {unit}
          </Typography>
        )}
      </Box>

      {progress !== undefined && (
        <LinearProgress
          variant="determinate"
          value={progress}
          color={color}
          sx={{ mt: 'auto', height: 6, borderRadius: 1 }}
        />
      )}
    </Paper>
  );
};

export const MetricsDashboard: React.FC = () => {
  const connectionStatus = useStore((state) => state.connectionStatus);
  const [metrics, setMetrics] = useState({
    sttLatency: 0,
    nlpLatency: 0,
    summaryLatency: 0,
    audioQuality: 0,
    totalSegments: 0,
  });

  // Simulate metrics updates
  useEffect(() => {
    if (connectionStatus !== 'connected') return;

    const interval = setInterval(() => {
      setMetrics({
        sttLatency: Math.floor(Math.random() * 100) + 50, // 50-150ms
        nlpLatency: Math.floor(Math.random() * 50) + 20, // 20-70ms
        summaryLatency: Math.floor(Math.random() * 200) + 100, // 100-300ms
        audioQuality: Math.floor(Math.random() * 20) + 80, // 80-100%
        totalSegments: Math.floor(Math.random() * 5) + metrics.totalSegments,
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [connectionStatus]);

  const getTotalLatency = () => {
    return metrics.sttLatency + metrics.nlpLatency + metrics.summaryLatency;
  };

  const getLatencyColor = (latency: number): 'success' | 'warning' | 'error' => {
    if (latency < 100) return 'success';
    if (latency < 200) return 'warning';
    return 'error';
  };

  const getQualityColor = (quality: number): 'success' | 'warning' | 'error' => {
    if (quality >= 90) return 'success';
    if (quality >= 70) return 'warning';
    return 'error';
  };

  const getConnectionColor = (): 'success' | 'warning' | 'error' | 'default' => {
    switch (connectionStatus) {
      case 'connected':
        return 'success';
      case 'connecting':
      case 'reconnecting':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
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
        avatar={<DashboardIcon color="primary" />}
        title="Metrics Dashboard"
        titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
        subheader={
          <Box sx={{ mt: 1 }}>
            <Chip
              label={connectionStatus === 'connected' ? 'Live Metrics' : 'Disconnected'}
              size="small"
              color={getConnectionColor()}
            />
          </Box>
        }
        sx={{ pb: 1 }}
      />

      <CardContent
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
        <Grid container spacing={2}>
          {/* STT Latency */}
          <Grid item xs={12} sm={6}>
            <MetricCard
              title="STT Latency"
              value={metrics.sttLatency}
              unit="ms"
              color={getLatencyColor(metrics.sttLatency)}
              icon={<SpeedIcon />}
              progress={(metrics.sttLatency / 150) * 100}
            />
          </Grid>

          {/* NLP Latency */}
          <Grid item xs={12} sm={6}>
            <MetricCard
              title="NLP Processing"
              value={metrics.nlpLatency}
              unit="ms"
              color={getLatencyColor(metrics.nlpLatency)}
              icon={<MemoryIcon />}
              progress={(metrics.nlpLatency / 70) * 100}
            />
          </Grid>

          {/* Summary Latency */}
          <Grid item xs={12} sm={6}>
            <MetricCard
              title="Summary Generation"
              value={metrics.summaryLatency}
              unit="ms"
              color={getLatencyColor(metrics.summaryLatency)}
              icon={<CloudIcon />}
              progress={(metrics.summaryLatency / 300) * 100}
            />
          </Grid>

          {/* Audio Quality */}
          <Grid item xs={12} sm={6}>
            <MetricCard
              title="Audio Quality"
              value={metrics.audioQuality}
              unit="%"
              color={getQualityColor(metrics.audioQuality)}
              icon={<CheckCircleIcon />}
              progress={metrics.audioQuality}
            />
          </Grid>

          {/* Total Pipeline Latency */}
          <Grid item xs={12}>
            <Paper
              elevation={2}
              sx={{
                p: 2.5,
                background: (theme) =>
                  `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
                color: 'white',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography
                    variant="caption"
                    sx={{
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      opacity: 0.9,
                      letterSpacing: 0.5,
                    }}
                  >
                    Total Pipeline Latency
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, mt: 0.5 }}>
                    <Typography variant="h3" fontWeight={700}>
                      {getTotalLatency()}
                    </Typography>
                    <Typography variant="h6" sx={{ opacity: 0.8 }}>
                      ms
                    </Typography>
                  </Box>
                  <Typography variant="caption" sx={{ opacity: 0.7, mt: 0.5, display: 'block' }}>
                    End-to-end processing time
                  </Typography>
                </Box>
                <SpeedIcon sx={{ fontSize: 64, opacity: 0.3 }} />
              </Box>
            </Paper>
          </Grid>

          {/* System Stats */}
          <Grid item xs={12}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                System Statistics
              </Typography>
              <Grid container spacing={2} sx={{ mt: 0.5 }}>
                <Grid item xs={6}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Segments Processed
                    </Typography>
                    <Typography variant="h6" fontWeight={600} color="primary">
                      {metrics.totalSegments}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Status
                    </Typography>
                    <Typography variant="h6" fontWeight={600} color="success.main">
                      Active
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default MetricsDashboard;
