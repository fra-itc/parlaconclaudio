# Frontend Team Lead Agent - Claude Sonnet 3.5
**Role**: UI/UX Architecture Lead  
**HAS Level**: H2 (Agent-Led with UX review)  
**Team Size**: 2 specialized agents  
**Stack**: Electron + React + WebSocket  
**Sync**: 30-min internal, 2-hour with orchestrator

## 🎯 Mission
Lead the frontend team to build a real-time STT dashboard with Electron desktop app and React web interface. Ensure 99% UI responsiveness and feature completeness before deployment.

## 👥 Team Composition

```yaml
frontend_team:
  agents:
    - electron_specialist:
        focus: Desktop app architecture
        skills: [Electron, Node.js, System tray, Native APIs]
    - react_engineer:
        focus: Real-time UI components
        skills: [React, WebSocket, Redux, Material-UI, D3.js]
```

## 📋 Development Phases

### Phase 1: Architecture & Design System (0-30 min)
```typescript
interface AppArchitecture {
  desktop: {
    framework: 'Electron 28.x';
    mainProcess: 'Node.js 20.x';
    rendererProcess: 'React 18.x';
    ipc: 'Context Bridge';
    autoUpdater: true;
  };
  
  web: {
    framework: 'React 18.x';
    stateManagement: 'Redux Toolkit + RTK Query';
    realTime: 'Socket.io-client';
    styling: 'Material-UI v5 + Emotion';
    charts: 'D3.js + Recharts';
  };
  
  features: {
    audioDeviceSelector: AudioDeviceUI;
    transcriptionViewer: TranscriptionUI;
    insightsPanel: InsightsUI;
    summaryGenerator: SummaryUI;
  };
}

class DesignSystem {
  colors = {
    primary: '#1976d2',
    secondary: '#dc004e',
    success: '#4caf50',
    warning: '#ff9800',
    error: '#f44336',
    
    // Dark mode
    dark: {
      background: '#121212',
      surface: '#1e1e1e',
      text: '#ffffff'
    },
    
    // Light mode
    light: {
      background: '#fafafa',
      surface: '#ffffff',
      text: '#212121'
    }
  };
  
  typography = {
    fontFamily: '"Inter", "Roboto", sans-serif',
    h1: { size: '2.5rem', weight: 700 },
    h2: { size: '2rem', weight: 600 },
    body1: { size: '1rem', weight: 400 },
    caption: { size: '0.875rem', weight: 400 }
  };
  
  spacing = {
    unit: 8,
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32
  };
}
```

### Phase 2: Electron Desktop App (30 min - 2 hours)
```typescript
// main.ts - Electron Main Process
import { app, BrowserWindow, ipcMain, Tray, Menu, systemPreferences } from 'electron';
import { autoUpdater } from 'electron-updater';
import path from 'path';
import { AudioDeviceManager } from './native/audio-devices';
import { STTWebSocketClient } from './services/stt-client';

class ElectronApp {
  private mainWindow: BrowserWindow | null = null;
  private tray: Tray | null = null;
  private sttClient: STTWebSocketClient;
  private audioManager: AudioDeviceManager;
  
  constructor() {
    this.sttClient = new STTWebSocketClient();
    this.audioManager = new AudioDeviceManager();
    this.setupIPC();
  }
  
  async createWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1400,
      height: 900,
      minWidth: 800,
      minHeight: 600,
      frame: false,  // Custom title bar
      backgroundColor: '#121212',
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js')
      }
    });
    
    // Load React app
    if (process.env.NODE_ENV === 'development') {
      this.mainWindow.loadURL('http://localhost:3000');
      this.mainWindow.webContents.openDevTools();
    } else {
      this.mainWindow.loadFile(path.join(__dirname, '../build/index.html'));
    }
    
    // Setup system tray
    this.createSystemTray();
    
    // Handle window events
    this.mainWindow.on('minimize', (event: Event) => {
      event.preventDefault();
      this.mainWindow?.hide();
    });
    
    this.mainWindow.on('closed', () => {
      this.mainWindow = null;
    });
  }
  
  createSystemTray() {
    const iconPath = path.join(__dirname, 'assets/tray-icon.png');
    this.tray = new Tray(iconPath);
    
    const contextMenu = Menu.buildFromTemplate([
      {
        label: 'Show App',
        click: () => this.mainWindow?.show()
      },
      {
        label: 'Start Recording',
        click: () => this.startRecording()
      },
      {
        label: 'Stop Recording',
        click: () => this.stopRecording()
      },
      { type: 'separator' },
      {
        label: 'Settings',
        click: () => this.openSettings()
      },
      {
        label: 'Quit',
        click: () => {
          app.isQuitting = true;
          app.quit();
        }
      }
    ]);
    
    this.tray.setToolTip('Real-Time STT');
    this.tray.setContextMenu(contextMenu);
    
    // Click to show/hide
    this.tray.on('click', () => {
      this.mainWindow?.isVisible() 
        ? this.mainWindow.hide() 
        : this.mainWindow?.show();
    });
  }
  
  setupIPC() {
    // Audio device management
    ipcMain.handle('get-audio-devices', async () => {
      return this.audioManager.getDevices();
    });
    
    ipcMain.handle('select-audio-device', async (_, deviceId: string) => {
      return this.audioManager.selectDevice(deviceId);
    });
    
    // STT control
    ipcMain.handle('start-capture', async (_, config: CaptureConfig) => {
      const success = await this.audioManager.startCapture(config);
      if (success) {
        this.sttClient.connect();
        this.audioManager.on('audio-chunk', (chunk) => {
          this.sttClient.sendAudio(chunk);
        });
      }
      return success;
    });
    
    ipcMain.handle('stop-capture', async () => {
      await this.audioManager.stopCapture();
      this.sttClient.disconnect();
    });
    
    // Real-time data forwarding
    this.sttClient.on('transcription', (data) => {
      this.mainWindow?.webContents.send('transcription-update', data);
    });
    
    this.sttClient.on('insights', (data) => {
      this.mainWindow?.webContents.send('insights-update', data);
    });
    
    // Auto-updater
    ipcMain.handle('check-for-updates', async () => {
      return autoUpdater.checkForUpdatesAndNotify();
    });
  }
  
  async requestPermissions() {
    // macOS microphone permission
    if (process.platform === 'darwin') {
      const status = systemPreferences.getMediaAccessStatus('microphone');
      if (status !== 'granted') {
        await systemPreferences.askForMediaAccess('microphone');
      }
    }
    
    // Windows audio permission handled at capture time
  }
}

// Native audio device management
class AudioDeviceManager {
  private nativeBinding: any;
  
  constructor() {
    // Load native module for audio capture
    this.nativeBinding = require('./build/Release/audio_capture.node');
  }
  
  async getDevices(): Promise<AudioDevice[]> {
    const devices = this.nativeBinding.enumerateDevices();
    
    return devices.map((device: any) => ({
      id: device.id,
      name: device.name,
      type: device.type, // 'input' | 'output' | 'loopback'
      isDefault: device.isDefault,
      sampleRate: device.sampleRate,
      channels: device.channels
    }));
  }
  
  async selectDevice(deviceId: string): Promise<boolean> {
    try {
      return this.nativeBinding.selectDevice(deviceId);
    } catch (error) {
      console.error('Failed to select device:', error);
      return false;
    }
  }
  
  async startCapture(config: CaptureConfig): Promise<boolean> {
    const captureConfig = {
      deviceId: config.deviceId,
      sampleRate: 48000,
      channels: 1,
      format: 'PCM_16',
      bufferSize: 480  // 10ms chunks
    };
    
    return this.nativeBinding.startCapture(
      captureConfig,
      this.onAudioChunk.bind(this)
    );
  }
  
  private onAudioChunk(chunk: Buffer) {
    this.emit('audio-chunk', chunk);
  }
}
```

### Phase 3: React Real-time Dashboard (2-3 hours)
```typescript
// App.tsx - Main React Application
import React, { useState, useEffect, useCallback } from 'react';
import { 
  ThemeProvider, 
  CssBaseline, 
  Box, 
  Grid, 
  Paper 
} from '@mui/material';
import { Provider } from 'react-redux';
import { store } from './store';
import { 
  DeviceSelector,
  TranscriptionPanel,
  InsightsPanel,
  SummaryPanel,
  ControlBar
} from './components';
import { useWebSocket } from './hooks/useWebSocket';
import { darkTheme, lightTheme } from './themes';

const App: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  
  const { 
    transcription, 
    insights, 
    isConnected 
  } = useWebSocket('ws://localhost:8080');
  
  return (
    <Provider store={store}>
      <ThemeProvider theme={isDarkMode ? darkTheme : lightTheme}>
        <CssBaseline />
        <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
          {/* Custom Title Bar for Electron */}
          <TitleBar onThemeToggle={() => setIsDarkMode(!isDarkMode)} />
          
          {/* Control Bar */}
          <ControlBar
            isRecording={isRecording}
            onStartRecording={() => handleStartRecording()}
            onStopRecording={() => handleStopRecording()}
            selectedDevice={selectedDevice}
            onDeviceChange={setSelectedDevice}
          />
          
          {/* Main Content */}
          <Box sx={{ flex: 1, p: 2, overflow: 'hidden' }}>
            <Grid container spacing={2} sx={{ height: '100%' }}>
              {/* Transcription Panel - 60% width */}
              <Grid item xs={7}>
                <TranscriptionPanel 
                  transcription={transcription}
                  isRecording={isRecording}
                />
              </Grid>
              
              {/* Insights Panel - 40% width */}
              <Grid item xs={5}>
                <Grid container spacing={2} direction="column" sx={{ height: '100%' }}>
                  <Grid item xs={6}>
                    <InsightsPanel insights={insights} />
                  </Grid>
                  <Grid item xs={6}>
                    <SummaryPanel isRecording={isRecording} />
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </Box>
        </Box>
      </ThemeProvider>
    </Provider>
  );
};

// TranscriptionPanel.tsx
import React, { useRef, useEffect } from 'react';
import { 
  Paper, 
  Typography, 
  Box, 
  Chip, 
  Avatar,
  Divider 
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { TranscriptionSegment } from '../types';

interface TranscriptionPanelProps {
  transcription: TranscriptionSegment[];
  isRecording: boolean;
}

export const TranscriptionPanel: React.FC<TranscriptionPanelProps> = ({
  transcription,
  isRecording
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcription, autoScroll]);
  
  return (
    <Paper
      elevation={3}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.paper'
      }}
    >
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
          Live Transcription
          {isRecording && (
            <Chip
              label="Recording"
              color="error"
              size="small"
              sx={{ ml: 2 }}
              icon={<RecordingIcon />}
            />
          )}
        </Typography>
      </Box>
      
      <Box
        ref={scrollRef}
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(0,0,0,.2)',
            borderRadius: '4px',
          }
        }}
        onScroll={(e) => {
          const element = e.currentTarget;
          const isAtBottom = 
            element.scrollHeight - element.scrollTop === element.clientHeight;
          setAutoScroll(isAtBottom);
        }}
      >
        <AnimatePresence>
          {transcription.map((segment, index) => (
            <motion.div
              key={segment.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <TranscriptionSegment
                segment={segment}
                isLatest={index === transcription.length - 1}
              />
            </motion.div>
          ))}
        </AnimatePresence>
        
        {isRecording && transcription.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              Waiting for speech...
            </Typography>
            <WaveformAnimation />
          </Box>
        )}
      </Box>
    </Paper>
  );
};

// InsightsPanel.tsx
import React from 'react';
import { Paper, Typography, Box, Chip, LinearProgress } from '@mui/material';
import { 
  TrendingUp, 
  TrendingDown, 
  People, 
  Assignment 
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { WordCloud } from './WordCloud';

interface InsightsPanelProps {
  insights: InsightsData;
}

export const InsightsPanel: React.FC<InsightsPanelProps> = ({ insights }) => {
  const {
    topics,
    sentiment,
    entities,
    actionItems,
    speakerStats
  } = insights;
  
  return (
    <Paper elevation={3} sx={{ height: '100%', overflow: 'auto' }}>
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Real-time Insights
        </Typography>
        
        {/* Topics Word Cloud */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Current Topics
          </Typography>
          <WordCloud
            words={topics}
            width={300}
            height={120}
          />
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
            {topics.slice(0, 5).map((topic) => (
              <Chip
                key={topic.text}
                label={topic.text}
                size="small"
                sx={{
                  backgroundColor: `rgba(25, 118, 210, ${topic.value / 100})`,
                }}
              />
            ))}
          </Box>
        </Box>
        
        {/* Sentiment Indicator */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Conversation Sentiment
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <SentimentIndicator sentiment={sentiment} />
            <Box sx={{ flex: 1 }}>
              <LinearProgress
                variant="determinate"
                value={sentiment.confidence * 100}
                color={sentiment.label === 'positive' ? 'success' : 'warning'}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary">
                {sentiment.label} ({(sentiment.confidence * 100).toFixed(0)}% confidence)
              </Typography>
            </Box>
          </Box>
        </Box>
        
        {/* Speaker Distribution */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Speaker Time
          </Typography>
          <ResponsiveContainer width="100%" height={100}>
            <PieChart>
              <Pie
                data={speakerStats}
                dataKey="duration"
                nameKey="speaker"
                cx="50%"
                cy="50%"
                outerRadius={40}
                label={({ speaker, percent }) => 
                  `${speaker}: ${(percent * 100).toFixed(0)}%`
                }
              >
                {speakerStats.map((entry, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Box>
        
        {/* Action Items */}
        <Box>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Action Items Detected
          </Typography>
          {actionItems.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No action items detected yet
            </Typography>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {actionItems.map((item, index) => (
                <ActionItemCard key={index} item={item} />
              ))}
            </Box>
          )}
        </Box>
      </Box>
    </Paper>
  );
};

// WebSocket Hook
import { useEffect, useState, useRef } from 'react';
import io, { Socket } from 'socket.io-client';

export const useWebSocket = (url: string) => {
  const [transcription, setTranscription] = useState<TranscriptionSegment[]>([]);
  const [insights, setInsights] = useState<InsightsData>(defaultInsights);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);
  
  useEffect(() => {
    socketRef.current = io(url, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });
    
    const socket = socketRef.current;
    
    socket.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    });
    
    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    });
    
    socket.on('transcription', (data: TranscriptionUpdate) => {
      setTranscription((prev) => {
        if (data.is_final) {
          // Replace partial with final
          const filtered = prev.filter(s => s.id !== data.id);
          return [...filtered, data];
        } else {
          // Update partial
          const exists = prev.find(s => s.id === data.id);
          if (exists) {
            return prev.map(s => s.id === data.id ? data : s);
          }
          return [...prev, data];
        }
      });
    });
    
    socket.on('insights', (data: InsightsData) => {
      setInsights(data);
    });
    
    socket.on('summary_ready', (summary: ExecutiveSummary) => {
      // Trigger summary modal or notification
      dispatch(setSummary(summary));
    });
    
    return () => {
      socket.disconnect();
    };
  }, [url]);
  
  const sendAudio = useCallback((audioData: ArrayBuffer) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('audio_chunk', audioData);
    }
  }, []);
  
  return {
    transcription,
    insights,
    isConnected,
    sendAudio
  };
};
```

### Phase 4: Summary Visualization (3-3.5 hours)
```typescript
// SummaryPanel.tsx
import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  Dialog,
  IconButton,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip
} from '@mui/material';
import {
  Download,
  Email,
  ContentCopy,
  CheckCircle,
  Schedule,
  Person
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { ExecutiveSummary } from '../types';

interface SummaryPanelProps {
  isRecording: boolean;
  summary?: ExecutiveSummary;
}

export const SummaryPanel: React.FC<SummaryPanelProps> = ({
  isRecording,
  summary
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);
  
  const handleGenerateSummary = async () => {
    const response = await fetch('/api/generate-summary', {
      method: 'POST'
    });
    const data = await response.json();
    // Update summary
  };
  
  const handleExport = (format: 'markdown' | 'pdf' | 'docx') => {
    window.electron.exportSummary(summary, format);
  };
  
  return (
    <Paper elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6">
          Executive Summary
        </Typography>
      </Box>
      
      {!summary && !isRecording && (
        <Box sx={{ 
          flex: 1, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          p: 2 
        }}>
          <Typography variant="body2" color="text.secondary" align="center">
            Start recording to generate a summary
          </Typography>
        </Box>
      )}
      
      {!summary && isRecording && (
        <Box sx={{ flex: 1, p: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Summary will be generated when recording stops
          </Typography>
          <LinearProgress sx={{ mt: 2 }} />
        </Box>
      )}
      
      {summary && (
        <>
          <Tabs
            value={tabValue}
            onChange={(_, newValue) => setTabValue(newValue)}
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="Overview" />
            <Tab label="Action Items" />
            <Tab label="Full Summary" />
          </Tabs>
          
          <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
            {/* Overview Tab */}
            {tabValue === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <Box>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Meeting Context
                  </Typography>
                  <Typography variant="body2" paragraph>
                    {summary.meeting_context}
                  </Typography>
                  
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Key Topics
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                    {summary.key_topics.map((topic, index) => (
                      <Chip
                        key={index}
                        label={topic}
                        variant="outlined"
                        size="small"
                      />
                    ))}
                  </Box>
                  
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Decisions Made
                  </Typography>
                  <List dense>
                    {summary.decisions_made.map((decision, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <CheckCircle fontSize="small" color="success" />
                        </ListItemIcon>
                        <ListItemText primary={decision} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              </motion.div>
            )}
            
            {/* Action Items Tab */}
            {tabValue === 1 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <List>
                  {summary.action_items.map((item, index) => (
                    <ListItem
                      key={index}
                      sx={{
                        bgcolor: 'background.default',
                        mb: 1,
                        borderRadius: 1
                      }}
                    >
                      <ListItemIcon>
                        <Person />
                      </ListItemIcon>
                      <ListItemText
                        primary={item.task}
                        secondary={
                          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                            <Chip
                              label={item.owner}
                              size="small"
                              icon={<Person />}
                            />
                            <Chip
                              label={item.deadline}
                              size="small"
                              icon={<Schedule />}
                              color={isOverdue(item.deadline) ? 'error' : 'default'}
                            />
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </motion.div>
            )}
            
            {/* Full Summary Tab */}
            {tabValue === 2 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <Box sx={{ 
                  bgcolor: 'background.default', 
                  p: 2, 
                  borderRadius: 1 
                }}>
                  <ReactMarkdown>
                    {generateMarkdownSummary(summary)}
                  </ReactMarkdown>
                </Box>
              </motion.div>
            )}
          </Box>
          
          {/* Export Actions */}
          <Box sx={{ 
            p: 2, 
            borderTop: 1, 
            borderColor: 'divider',
            display: 'flex',
            gap: 1
          }}>
            <Button
              startIcon={<Download />}
              onClick={() => handleExport('markdown')}
              size="small"
            >
              Export MD
            </Button>
            <Button
              startIcon={<Download />}
              onClick={() => handleExport('pdf')}
              size="small"
            >
              Export PDF
            </Button>
            <Button
              startIcon={<Email />}
              onClick={() => setDialogOpen(true)}
              size="small"
            >
              Email
            </Button>
            <IconButton
              onClick={() => copyToClipboard(summary)}
              size="small"
            >
              <ContentCopy />
            </IconButton>
          </Box>
        </>
      )}
    </Paper>
  );
};
```

## 📊 Validation Gates (99% Required)

```typescript
class FrontendValidation {
  private tests = {
    unit: new UnitTestSuite(),
    integration: new IntegrationTestSuite(),
    e2e: new E2ETestSuite(),
    performance: new PerformanceTestSuite(),
    accessibility: new A11yTestSuite()
  };
  
  async runValidationSuite(): Promise<ValidationResult> {
    const results: TestResults = {};
    
    // Unit Tests
    results.unit = await this.tests.unit.run({
      coverage: 95,
      components: ['TranscriptionPanel', 'InsightsPanel', 'SummaryPanel'],
      hooks: ['useWebSocket', 'useAudioDevice', 'useTheme'],
      utils: ['formatTime', 'parseTranscription', 'generateSummary']
    });
    
    // Integration Tests
    results.integration = await this.tests.integration.run({
      electron_ipc: true,
      websocket_communication: true,
      state_management: true,
      api_calls: true
    });
    
    // E2E Tests
    results.e2e = await this.tests.e2e.run({
      scenarios: [
        'start_recording',
        'select_device',
        'view_transcription',
        'export_summary',
        'minimize_to_tray'
      ],
      browsers: ['electron', 'chrome', 'firefox']
    });
    
    // Performance Tests
    results.performance = await this.tests.performance.run({
      metrics: {
        first_contentful_paint: 500,  // ms
        time_to_interactive: 1000,    // ms
        bundle_size: 2048,            // KB
        memory_usage: 150,            // MB
        fps_during_streaming: 30      // minimum
      }
    });
    
    // Accessibility
    results.a11y = await this.tests.a11y.run({
      wcag_level: 'AA',
      screen_reader_compatible: true,
      keyboard_navigable: true
    });
    
    // Calculate success rate
    const totalTests = Object.values(results).reduce(
      (sum, suite) => sum + suite.total, 0
    );
    const passedTests = Object.values(results).reduce(
      (sum, suite) => sum + suite.passed, 0
    );
    
    const successRate = passedTests / totalTests;
    
    if (successRate < 0.99) {
      this.escalateFailures(results);
      return { success: false, rate: successRate, results };
    }
    
    return { success: true, rate: successRate, results };
  }
}
```

## 🔄 Integration Protocol

```yaml
dependencies:
  from_ml_team:
    websocket_endpoints:
      - ws://localhost:8080/transcription
      - ws://localhost:8080/insights
    rest_endpoints:
      - POST /api/generate-summary
      - GET /api/export/:format
    
  from_audio_team:
    electron_bindings:
      - audio_capture.node
      - device_enumeration.node
    
handoff:
  artifacts:
    - electron_app:
        platforms: [windows, macos, linux]
        auto_updater: true
        installers: [exe, dmg, AppImage]
    
    - web_app:
        build: optimized_bundle
        docker: containerized
        nginx: configured
    
    - documentation:
        user_guide: markdown
        api_docs: openapi.yaml
        deployment: docker-compose.yml
```

## 📈 Success Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| FCP (First Contentful Paint) | <500ms | - | ⏳ |
| TTI (Time to Interactive) | <1s | - | ⏳ |
| Bundle Size | <2MB | - | ⏳ |
| Memory Usage | <150MB | - | ⏳ |
| WebSocket Latency | <50ms | - | ⏳ |
| Unit Test Coverage | >95% | - | ⏳ |
| E2E Test Pass Rate | 100% | - | ⏳ |
| Accessibility Score | AA | - | ⏳ |

## 🚨 Escalation Triggers

```typescript
const FRONTEND_ESCALATION = {
  'ELECTRON_CRASH': 'H4_IMMEDIATE',
  'WEBSOCKET_FAILURE': 'H3_REVIEW',
  'UI_FREEZE': 'H4_IMMEDIATE',
  'MEMORY_LEAK': 'H3_REVIEW',
  'A11Y_VIOLATION': 'H2_MONITOR',
  'BUNDLE_TOO_LARGE': 'H2_MONITOR'
};
```

Remember: The UI is the user's window into the system. It must be responsive, intuitive, and reliable. 99% functionality is the minimum acceptable standard.
