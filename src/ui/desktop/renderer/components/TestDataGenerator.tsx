import React from 'react';
import { useStore } from '../store';
import { Button } from './ui';

/**
 * TestDataGenerator.tsx
 *
 * A utility component for populating the store with sample data
 * to test and visualize the SummaryPanel and SettingsPanel components.
 *
 * Usage:
 * Add this component to your App or testing layout, click the buttons
 * to generate sample data, then view it in the panels.
 */

export const TestDataGenerator: React.FC = () => {
  const { addSummary, clearSummaries, clearAll } = useStore();

  const generateSampleSummaries = () => {
    const summaries = [
      {
        id: 'summary-1',
        content: 'The team discussed the quarterly performance metrics and identified key areas for improvement. The main focus was on customer satisfaction scores and operational efficiency. Several action items were assigned to department leads.',
        keyPoints: [
          'Q4 revenue exceeded targets by 12%',
          'Customer satisfaction score: 4.2/5.0',
          'Need to improve response time by 15%',
          'New hiring initiative approved for Q1',
        ],
        timestamp: Date.now() - 3600000 * 2, // 2 hours ago
      },
      {
        id: 'summary-2',
        content: 'Technical architecture review meeting covered the migration strategy for the new cloud infrastructure. The team evaluated different providers and discussed security compliance requirements. A phased rollout plan was proposed.',
        keyPoints: [
          'AWS selected as primary cloud provider',
          'Migration timeline: 6 months',
          'Security audit scheduled for next month',
          'Estimated cost savings: $200K annually',
        ],
        timestamp: Date.now() - 3600000 * 1, // 1 hour ago
      },
      {
        id: 'summary-3',
        content: 'Product roadmap planning session for the next release cycle. Prioritized features based on user feedback and market research. Discussed resource allocation and potential risks.',
        keyPoints: [
          'Top priority: Mobile app redesign',
          'New AI-powered search feature',
          'Integration with third-party tools',
          'Expected release: End of Q2',
        ],
        timestamp: Date.now() - 3600000 * 0.5, // 30 minutes ago
      },
      {
        id: 'summary-4',
        content: 'This is the most recent summary discussing the latest sprint retrospective. The team reflected on what went well, what could be improved, and action items for the next sprint. Overall sentiment was positive with strong team collaboration.',
        keyPoints: [
          'Velocity improved by 20% this sprint',
          'Better communication across teams',
          'Need to reduce technical debt',
          'Bi-weekly code reviews working well',
        ],
        timestamp: Date.now(), // Now
      },
    ];

    summaries.forEach((summary) => addSummary(summary));
  };

  const generateSingleSummary = () => {
    const summary = {
      id: `summary-${Date.now()}`,
      content: `New summary generated at ${new Date().toLocaleTimeString()}. This summary contains important information about recent events and discussions. It demonstrates how the summary panel handles new entries and updates the current summary view.`,
      keyPoints: [
        `Generated at ${new Date().toLocaleTimeString()}`,
        'Demonstrates real-time updates',
        'Shows latest summary highlighting',
      ],
      timestamp: Date.now(),
    };

    addSummary(summary);
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 max-w-2xl mx-auto">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white mb-2">
          Test Data Generator
        </h3>
        <p className="text-sm text-gray-400">
          Use these buttons to populate the store with sample data for testing the panels.
        </p>
      </div>

      <div className="space-y-3">
        <div className="flex gap-3">
          <Button variant="primary" onClick={generateSampleSummaries}>
            Generate Sample Summaries (4)
          </Button>
          <Button variant="secondary" onClick={generateSingleSummary}>
            Add Single Summary
          </Button>
        </div>

        <div className="flex gap-3">
          <Button variant="danger" onClick={clearSummaries}>
            Clear Summaries
          </Button>
          <Button variant="danger" onClick={clearAll}>
            Clear All Data
          </Button>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-gray-700">
        <h4 className="text-sm font-semibold text-gray-300 mb-2">
          Quick Test Scenarios
        </h4>
        <ul className="text-sm text-gray-400 space-y-2">
          <li className="flex items-start">
            <span className="text-blue-400 mr-2">1.</span>
            <span>Generate sample summaries, then open the Summary panel to see the latest summary with history</span>
          </li>
          <li className="flex items-start">
            <span className="text-blue-400 mr-2">2.</span>
            <span>Click "Show History" to view previous summaries and test the selection feature</span>
          </li>
          <li className="flex items-start">
            <span className="text-blue-400 mr-2">3.</span>
            <span>Test the copy to clipboard functionality on different summaries</span>
          </li>
          <li className="flex items-start">
            <span className="text-blue-400 mr-2">4.</span>
            <span>Open Settings panel and try changing values, then save to test validation</span>
          </li>
          <li className="flex items-start">
            <span className="text-blue-400 mr-2">5.</span>
            <span>Clear summaries to test the empty state in the Summary panel</span>
          </li>
        </ul>
      </div>
    </div>
  );
};
