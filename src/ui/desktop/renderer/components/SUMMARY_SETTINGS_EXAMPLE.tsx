import React, { useState } from 'react';
import { SummaryPanel } from './SummaryPanel';
import { SettingsPanel } from './SettingsPanel';

/**
 * SUMMARY_SETTINGS_EXAMPLE.tsx
 *
 * This component demonstrates how to integrate SummaryPanel and SettingsPanel
 * into your application. It shows two different layout options:
 * 1. Tabbed Interface - Switch between panels using tabs
 * 2. Side-by-Side Layout - Display both panels simultaneously
 *
 * Usage:
 * Import this component into your App.tsx or main layout component
 * and render it where you want the panels to appear.
 */

type PanelView = 'summary' | 'settings';

// Example 1: Tabbed Interface
export const TabbedPanelExample: React.FC = () => {
  const [activePanel, setActivePanel] = useState<PanelView>('summary');

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Tab Navigation */}
      <div className="border-b border-gray-800">
        <nav className="flex">
          <button
            onClick={() => setActivePanel('summary')}
            className={`
              px-6 py-3 font-medium text-sm transition-colors border-b-2
              ${
                activePanel === 'summary'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }
            `}
          >
            Summary
          </button>
          <button
            onClick={() => setActivePanel('settings')}
            className={`
              px-6 py-3 font-medium text-sm transition-colors border-b-2
              ${
                activePanel === 'settings'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }
            `}
          >
            Settings
          </button>
        </nav>
      </div>

      {/* Panel Content */}
      <div className="flex-1 overflow-hidden">
        {activePanel === 'summary' && <SummaryPanel />}
        {activePanel === 'settings' && <SettingsPanel />}
      </div>
    </div>
  );
};

// Example 2: Side-by-Side Layout
export const SideBySidePanelExample: React.FC = () => {
  return (
    <div className="h-screen flex bg-gray-900">
      {/* Left Panel - Summary */}
      <div className="flex-1 border-r border-gray-800 overflow-hidden">
        <SummaryPanel />
      </div>

      {/* Right Panel - Settings */}
      <div className="flex-1 overflow-hidden">
        <SettingsPanel />
      </div>
    </div>
  );
};

// Example 3: Collapsible Sidebar with Main Content
export const SidebarPanelExample: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarContent, setSidebarContent] = useState<'summary' | 'settings'>('summary');

  return (
    <div className="h-screen flex bg-gray-900">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        <div className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-white">ORCHIDEA RTSTT</h1>
          <div className="flex gap-2">
            <button
              onClick={() => {
                setSidebarContent('summary');
                setSidebarOpen(true);
              }}
              className="px-3 py-2 text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-800 rounded-md transition-colors"
            >
              Summary
            </button>
            <button
              onClick={() => {
                setSidebarContent('settings');
                setSidebarOpen(true);
              }}
              className="px-3 py-2 text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-800 rounded-md transition-colors"
            >
              Settings
            </button>
          </div>
        </div>

        <div className="flex-1 p-6 overflow-y-auto">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold text-white mb-4">
              Your Main Content Here
            </h2>
            <p className="text-gray-400">
              This is where your transcription view, insights, or other main content would go.
              The sidebar panels can be toggled using the buttons in the header.
            </p>
          </div>
        </div>
      </div>

      {/* Collapsible Sidebar */}
      {sidebarOpen && (
        <div className="w-96 border-l border-gray-800 flex flex-col">
          <div className="border-b border-gray-800 px-4 py-3 flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-300">
              {sidebarContent === 'summary' ? 'Summary' : 'Settings'}
            </h3>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <div className="flex-1 overflow-hidden">
            {sidebarContent === 'summary' ? <SummaryPanel /> : <SettingsPanel />}
          </div>
        </div>
      )}
    </div>
  );
};

// Example 4: Modal/Overlay Approach
export const ModalPanelExample: React.FC = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState<'summary' | 'settings'>('summary');

  const openModal = (content: 'summary' | 'settings') => {
    setModalContent(content);
    setModalOpen(true);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">ORCHIDEA RTSTT</h1>
        <div className="flex gap-2">
          <button
            onClick={() => openModal('summary')}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
          >
            View Summary
          </button>
          <button
            onClick={() => openModal('settings')}
            className="px-4 py-2 text-sm font-medium text-white bg-gray-700 hover:bg-gray-600 rounded-md transition-colors"
          >
            Settings
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-white mb-4">
            Main Application View
          </h2>
          <p className="text-gray-400">
            Click the buttons in the header to open Summary or Settings in a modal overlay.
          </p>
        </div>
      </div>

      {/* Modal Overlay */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={() => setModalOpen(false)}
          />

          {/* Modal Content */}
          <div className="relative w-full max-w-4xl h-[90vh] bg-gray-900 rounded-lg shadow-2xl overflow-hidden">
            <button
              onClick={() => setModalOpen(false)}
              className="absolute top-4 right-4 z-10 text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
            {modalContent === 'summary' ? <SummaryPanel /> : <SettingsPanel />}
          </div>
        </div>
      )}
    </div>
  );
};

// Default Export - Choose your preferred layout
export default TabbedPanelExample;
