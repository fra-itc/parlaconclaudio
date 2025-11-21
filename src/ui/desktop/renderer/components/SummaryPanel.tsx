import React, { useState } from 'react';
import { useSummaries, useCurrentSummary, useStore } from '../store';
import { Button } from './ui';

export const SummaryPanel: React.FC = () => {
  const summaries = useSummaries();
  const currentSummary = useCurrentSummary();
  const { setCurrentSummary } = useStore();
  const [showHistory, setShowHistory] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Format timestamp for display
  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // Copy to clipboard handler
  const copyToClipboard = async (content: string, id: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  // Placeholder for regenerate functionality
  const handleRegenerate = () => {
    console.log('Regenerate summary - to be implemented');
  };

  // Empty state
  if (summaries.length === 0) {
    return (
      <div className="h-full flex flex-col bg-gray-900 text-white">
        <div className="border-b border-gray-800 px-6 py-4">
          <h2 className="text-xl font-semibold">Summary</h2>
        </div>
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center max-w-md">
            <svg
              className="mx-auto h-16 w-16 text-gray-600 mb-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="text-lg font-medium text-gray-300 mb-2">
              No Summaries Yet
            </h3>
            <p className="text-gray-400">
              Summaries will appear here once they are generated from your transcriptions.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Get the latest summary if no current summary is selected
  const displaySummary = currentSummary || summaries[summaries.length - 1];

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Summary</h2>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="small"
              onClick={handleRegenerate}
              title="Regenerate summary"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </Button>
            {summaries.length > 1 && (
              <Button
                variant="secondary"
                size="small"
                onClick={() => setShowHistory(!showHistory)}
              >
                {showHistory ? 'Hide History' : 'Show History'}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Current/Latest Summary */}
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-lg font-semibold text-blue-400">
                  {currentSummary ? 'Current Summary' : 'Latest Summary'}
                </h3>
                {displaySummary.id === summaries[summaries.length - 1].id && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-900 text-green-200">
                    Latest
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-400">
                Generated on {formatTimestamp(displaySummary.timestamp)}
              </p>
            </div>
            <Button
              variant="secondary"
              size="small"
              onClick={() => copyToClipboard(displaySummary.content, displaySummary.id)}
              title="Copy to clipboard"
            >
              {copiedId === displaySummary.id ? (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
              )}
            </Button>
          </div>

          {/* Summary Content */}
          <div className="prose prose-invert max-w-none">
            <p className="text-gray-200 leading-relaxed whitespace-pre-wrap">
              {displaySummary.content}
            </p>
          </div>

          {/* Key Points */}
          {displaySummary.keyPoints && displaySummary.keyPoints.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Key Points
              </h4>
              <ul className="space-y-2">
                {displaySummary.keyPoints.map((point, index) => (
                  <li key={index} className="flex items-start">
                    <svg
                      className="w-5 h-5 text-blue-500 mr-2 mt-0.5 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-gray-300">{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* History Section */}
        {showHistory && summaries.length > 1 && (
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-300">
              Previous Summaries ({summaries.length - 1})
            </h3>
            <div className="space-y-4">
              {summaries
                .slice()
                .reverse()
                .slice(1) // Skip the first one (latest) as it's already displayed above
                .map((summary) => (
                  <div
                    key={summary.id}
                    className={`
                      p-4 rounded-lg border cursor-pointer transition-all
                      ${
                        currentSummary?.id === summary.id
                          ? 'border-blue-500 bg-blue-950'
                          : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                      }
                    `}
                    onClick={() => setCurrentSummary(summary)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <p className="text-sm text-gray-400">
                        {formatTimestamp(summary.timestamp)}
                      </p>
                      <Button
                        variant="secondary"
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          copyToClipboard(summary.content, summary.id);
                        }}
                        title="Copy to clipboard"
                      >
                        {copiedId === summary.id ? (
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        ) : (
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                            />
                          </svg>
                        )}
                      </Button>
                    </div>
                    <p className="text-gray-300 text-sm line-clamp-3">
                      {summary.content}
                    </p>
                    {summary.keyPoints && summary.keyPoints.length > 0 && (
                      <p className="text-xs text-gray-500 mt-2">
                        {summary.keyPoints.length} key point{summary.keyPoints.length !== 1 ? 's' : ''}
                      </p>
                    )}
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
