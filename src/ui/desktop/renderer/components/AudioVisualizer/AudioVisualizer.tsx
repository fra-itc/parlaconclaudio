import React, { useRef, useEffect, useState } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Box,
  Fab,
  IconButton,
  Typography,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  Mic as MicIcon,
  Stop as StopIcon,
  VolumeUp as VolumeUpIcon,
  VolumeOff as VolumeOffIcon,
  GraphicEq as GraphicEqIcon,
} from '@mui/icons-material';

interface AudioVisualizerProps {
  onRecordingStart?: () => void;
  onRecordingStop?: () => void;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  onRecordingStart,
  onRecordingStop,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(80);
  const [audioLevel, setAudioLevel] = useState(0);
  const [selectedDevice, setSelectedDevice] = useState('default');
  const [vadActive, setVadActive] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();

  // Simulate audio level changes
  useEffect(() => {
    if (!isRecording) return;

    const interval = setInterval(() => {
      // Simulate random audio levels
      const newLevel = Math.random() * 100;
      setAudioLevel(newLevel);

      // Simulate VAD (Voice Activity Detection)
      setVadActive(newLevel > 30);
    }, 100);

    return () => clearInterval(interval);
  }, [isRecording]);

  // Draw waveform visualization
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const resizeCanvas = () => {
      const parent = canvas.parentElement;
      if (parent) {
        canvas.width = parent.clientWidth;
        canvas.height = parent.clientHeight;
      }
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Animation loop
    const animate = () => {
      if (!canvas || !ctx) return;

      const width = canvas.width;
      const height = canvas.height;

      // Clear canvas
      ctx.fillStyle = '#1e1e1e';
      ctx.fillRect(0, 0, width, height);

      if (isRecording) {
        // Draw waveform
        ctx.strokeStyle = vadActive ? '#4caf50' : '#90caf9';
        ctx.lineWidth = 2;
        ctx.beginPath();

        const centerY = height / 2;
        const amplitude = (audioLevel / 100) * (height / 2) * 0.8;

        for (let x = 0; x < width; x++) {
          const y = centerY + Math.sin((x + Date.now() * 0.01) * 0.05) * amplitude;
          if (x === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }

        ctx.stroke();

        // Draw center line
        ctx.strokeStyle = '#3e3e42';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, centerY);
        ctx.lineTo(width, centerY);
        ctx.stroke();
      } else {
        // Draw idle state
        ctx.strokeStyle = '#3e3e42';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, height / 2);
        ctx.stroke();
      }

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isRecording, audioLevel, vadActive]);

  const handleRecordingToggle = () => {
    if (isRecording) {
      setIsRecording(false);
      setAudioLevel(0);
      setVadActive(false);
      onRecordingStop?.();
    } else {
      setIsRecording(true);
      onRecordingStart?.();
    }
  };

  const getAudioLevelColor = () => {
    if (audioLevel < 50) return 'success';
    if (audioLevel < 75) return 'warning';
    return 'error';
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
        avatar={<GraphicEqIcon color="primary" />}
        title="Audio Visualizer"
        subheader={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
            <Chip
              size="small"
              label={isRecording ? 'Recording' : 'Idle'}
              color={isRecording ? 'success' : 'default'}
              sx={{
                animation: isRecording ? 'pulse 1.5s ease-in-out infinite' : 'none',
              }}
            />
            {vadActive && (
              <Chip
                size="small"
                label="Voice Detected"
                color="primary"
                sx={{ animation: 'pulse 1s ease-in-out infinite' }}
              />
            )}
          </Box>
        }
        sx={{ pb: 1 }}
      />

      <CardContent
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          overflow: 'hidden',
          pt: 0,
        }}
      >
        {/* Waveform Canvas */}
        <Box
          sx={{
            flex: 1,
            position: 'relative',
            borderRadius: 1,
            border: '1px solid',
            borderColor: 'divider',
            overflow: 'hidden',
            minHeight: 120,
          }}
        >
          <canvas
            ref={canvasRef}
            style={{
              width: '100%',
              height: '100%',
              display: 'block',
            }}
          />
        </Box>

        {/* Audio Level Meter */}
        {isRecording && (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                Audio Level
              </Typography>
              <Typography variant="caption" color={`${getAudioLevelColor()}.main`} fontWeight={600}>
                {Math.round(audioLevel)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={audioLevel}
              color={getAudioLevelColor()}
              sx={{ height: 8, borderRadius: 1 }}
            />
          </Box>
        )}

        {/* Controls */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            flexWrap: 'wrap',
          }}
        >
          {/* Record Button */}
          <Tooltip title={isRecording ? 'Stop Recording' : 'Start Recording'}>
            <Fab
              color={isRecording ? 'error' : 'primary'}
              onClick={handleRecordingToggle}
              sx={{
                boxShadow: 3,
                '&:hover': {
                  boxShadow: 6,
                },
              }}
            >
              {isRecording ? <StopIcon /> : <MicIcon />}
            </Fab>
          </Tooltip>

          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
            {/* Device Selection */}
            <FormControl fullWidth size="small">
              <InputLabel>Microphone</InputLabel>
              <Select
                value={selectedDevice}
                label="Microphone"
                onChange={(e) => setSelectedDevice(e.target.value)}
                disabled={isRecording}
              >
                <MenuItem value="default">Default Microphone</MenuItem>
                <MenuItem value="device1">Microphone (Device 1)</MenuItem>
                <MenuItem value="device2">Microphone (Device 2)</MenuItem>
              </Select>
            </FormControl>

            {/* Volume Control */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Tooltip title={isMuted ? 'Unmute' : 'Mute'}>
                <IconButton
                  size="small"
                  onClick={() => setIsMuted(!isMuted)}
                  color={isMuted ? 'error' : 'default'}
                >
                  {isMuted ? <VolumeOffIcon /> : <VolumeUpIcon />}
                </IconButton>
              </Tooltip>
              <Slider
                value={isMuted ? 0 : volume}
                onChange={(_, value) => setVolume(value as number)}
                disabled={isMuted}
                size="small"
                sx={{ flex: 1 }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ minWidth: 35 }}>
                {isMuted ? 0 : volume}%
              </Typography>
            </Box>
          </Box>
        </Box>
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
