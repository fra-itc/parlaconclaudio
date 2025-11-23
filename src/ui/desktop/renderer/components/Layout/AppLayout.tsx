import React, { ReactNode } from 'react';
import {
  Box,
  AppBar as MuiAppBar,
  Toolbar,
  Typography,
  IconButton,
  Tooltip,
  Grid,
  Container,
} from '@mui/material';
import {
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useTheme } from '../../contexts/ThemeContext';
import { StatusBar } from './StatusBar';

interface AppLayoutProps {
  children: ReactNode;
  onSettingsClick?: () => void;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children, onSettingsClick }) => {
  const { mode, toggleTheme } = useTheme();

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
      }}
    >
      {/* App Bar */}
      <MuiAppBar position="static" elevation={0}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            ORCHIDEA RTSTT
          </Typography>

          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              mr: 2,
              display: { xs: 'none', sm: 'block' },
            }}
          >
            v1.0.0-POC
          </Typography>

          <Tooltip title={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}>
            <IconButton color="inherit" onClick={toggleTheme} sx={{ mr: 1 }}>
              {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>

          {onSettingsClick && (
            <Tooltip title="Settings">
              <IconButton color="inherit" onClick={onSettingsClick}>
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          )}
        </Toolbar>
      </MuiAppBar>

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flex: 1,
          overflow: 'hidden',
          bgcolor: 'background.default',
        }}
      >
        {children}
      </Box>

      {/* Status Bar */}
      <StatusBar />
    </Box>
  );
};

// GridLayout component for 2x2 panel arrangement
interface GridLayoutProps {
  topLeft: ReactNode;
  topRight: ReactNode;
  bottomLeft: ReactNode;
  bottomRight: ReactNode;
}

export const GridLayout: React.FC<GridLayoutProps> = ({
  topLeft,
  topRight,
  bottomLeft,
  bottomRight,
}) => {
  return (
    <Container
      maxWidth={false}
      sx={{
        height: '100%',
        p: 2,
        overflow: 'hidden',
      }}
    >
      <Grid
        container
        spacing={2}
        sx={{
          height: '100%',
          overflow: 'hidden',
        }}
      >
        {/* Top Left */}
        <Grid
          item
          xs={12}
          md={6}
          sx={{
            height: { xs: 'auto', md: '50%' },
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Box
            sx={{
              height: '100%',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {topLeft}
          </Box>
        </Grid>

        {/* Top Right */}
        <Grid
          item
          xs={12}
          md={6}
          sx={{
            height: { xs: 'auto', md: '50%' },
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Box
            sx={{
              height: '100%',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {topRight}
          </Box>
        </Grid>

        {/* Bottom Left */}
        <Grid
          item
          xs={12}
          md={6}
          sx={{
            height: { xs: 'auto', md: '50%' },
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Box
            sx={{
              height: '100%',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {bottomLeft}
          </Box>
        </Grid>

        {/* Bottom Right */}
        <Grid
          item
          xs={12}
          md={6}
          sx={{
            height: { xs: 'auto', md: '50%' },
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Box
            sx={{
              height: '100%',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {bottomRight}
          </Box>
        </Grid>
      </Grid>
    </Container>
  );
};
