import React from 'react';
import {
  Box,
  Typography,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Circle as CircleIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { useStore } from '../../store';

export const StatusBar: React.FC = () => {
  const connectionStatus = useStore((state) => state.connectionStatus);
  const lastConnectedAt = useStore((state) => state.lastConnectedAt);

  const getStatusColor = () => {
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

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'reconnecting':
        return 'Reconnecting...';
      case 'error':
        return 'Connection Error';
      case 'disconnected':
      default:
        return 'Disconnected';
    }
  };

  const formatTimestamp = (timestamp: number | null) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        px: 3,
        py: 1,
        borderTop: 1,
        borderColor: 'divider',
        bgcolor: 'background.paper',
        minHeight: 40,
      }}
    >
      {/* Left: Connection Status */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Tooltip title={`Last connected: ${formatTimestamp(lastConnectedAt)}`}>
          <Chip
            icon={<CircleIcon sx={{ fontSize: 12 }} />}
            label={getStatusText()}
            color={getStatusColor()}
            size="small"
            sx={{
              fontWeight: 500,
              '& .MuiChip-icon': {
                animation: connectionStatus === 'connecting' || connectionStatus === 'reconnecting'
                  ? 'pulse 1.5s ease-in-out infinite'
                  : 'none',
              },
            }}
          />
        </Tooltip>
      </Box>

      {/* Center: Framework Info */}
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: { xs: 'none', md: 'block' } }}
      >
        Electron + React + Vite | ORCHIDEA Framework v1.3
      </Typography>

      {/* Right: Performance Metrics (placeholder) */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Tooltip title="System Performance">
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <SpeedIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              Ready
            </Typography>
          </Box>
        </Tooltip>
      </Box>

      {/* Pulse animation */}
      <style>
        {`
          @keyframes pulse {
            0%, 100% {
              opacity: 1;
            }
            50% {
              opacity: 0.5;
            }
          }
        `}
      </style>
    </Box>
  );
};
