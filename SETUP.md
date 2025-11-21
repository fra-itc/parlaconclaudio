# ORCHIDEA RTSTT Frontend Setup

## React + Vite + Electron Base Setup

This document describes the React base setup with Vite for the ORCHIDEA RTSTT Electron application.

## Structure

```
RTSTT-frontend/
├── src/
│   └── ui/
│       └── desktop/
│           └── renderer/
│               ├── index.html      # HTML entry point
│               ├── main.tsx         # React render entry
│               └── App.tsx          # Main React component
├── public/                          # Static assets
├── vite.config.ts                   # Vite configuration for Electron
├── tsconfig.json                    # TypeScript configuration
├── tsconfig.node.json              # TypeScript config for Vite
├── .eslintrc.cjs                   # ESLint configuration
└── package.json                     # Dependencies and scripts
```

## Installation

```bash
cd C:\PROJECTS\RTSTT-frontend
npm install
```

## Development

To run the Vite dev server:

```bash
npm run dev
```

This will start the development server at `http://localhost:5173`

## Building

To build the renderer process:

```bash
npm run build
```

Output will be in `dist/renderer/`

## Type Checking

To check TypeScript types without building:

```bash
npm run type-check
```

## Linting

To lint the codebase:

```bash
npm run lint
```

## Current Features

### App.tsx Component

The main App component includes:

- **Header**: Displays the application title and version
- **Main Content Area**: Placeholder for future UI panels
  - Audio Waveform panel (to be implemented)
  - Controls panel (to be implemented)
  - Transcription Display panel (to be implemented)
- **Footer**: Status indicator and technology stack display

### Styling

- Dark theme with VS Code-inspired color scheme
- Inline styles for initial setup (will migrate to CSS modules or styled-components)
- Responsive flexbox layout
- Full viewport height/width

### Vite Configuration

The Vite config includes:

- React plugin with Fast Refresh
- Electron-specific base path (`./`)
- Custom root directory pointing to renderer
- Path aliases for clean imports:
  - `@/` → `src/`
  - `@renderer/` → `src/ui/desktop/renderer/`
  - `@components/` → `src/ui/desktop/renderer/components/`
  - `@hooks/` → `src/ui/desktop/renderer/hooks/`
  - `@utils/` → `src/ui/desktop/renderer/utils/`
  - `@types/` → `src/types/`
- Optimized for ES2020 target
- Source maps enabled for debugging
- HMR (Hot Module Replacement) enabled

## Next Steps

1. Install dependencies: `npm install`
2. Create Electron main process files
3. Add UI components (waveform, controls, transcription)
4. Integrate with backend API
5. Add state management (Context API or Redux)
6. Implement WebSocket connection for real-time updates

## Technologies

- **React 18.3.1**: UI library
- **Vite 5.3.3**: Build tool and dev server
- **TypeScript 5.5.3**: Type safety
- **Electron 31.2.0**: Desktop application framework
- **ESLint**: Code quality and consistency

## Notes

- The app uses React 18's new `createRoot` API
- Strict mode is enabled for better development warnings
- Content Security Policy is configured in index.html
- The app is ready for integration with Electron main process
