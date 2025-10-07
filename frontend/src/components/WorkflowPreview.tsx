/**
 * Workflow preview component showing execution structure
 */

import type { WorkflowPreview as WorkflowPreviewType } from '../types/api';

interface WorkflowPreviewProps {
  preview: WorkflowPreviewType | null;
  isLoading: boolean;
  onClose: () => void;
}

export function WorkflowPreview({ preview, isLoading, onClose }: WorkflowPreviewProps) {
  if (!preview && !isLoading) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gray-50 px-6 py-4 border-b flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Workflow Preview</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-gray-600">Loading preview...</div>
            </div>
          ) : preview ? (
            <div className="space-y-6">
              {/* Summary */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-600">Workflow Name</div>
                    <div className="font-semibold text-gray-900">{preview.workflow_name}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">Estimated Steps</div>
                    <div className="font-semibold text-gray-900">{preview.estimated_steps}</div>
                  </div>
                </div>
              </div>

              {/* Agents */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Agents ({preview.agents.length})
                </h3>
                <div className="space-y-3">
                  {preview.agents.map((agent, index) => (
                    <div
                      key={index}
                      className="bg-gray-50 border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="font-semibold text-gray-900">{agent.name}</div>
                          <div className="text-sm text-gray-600">Type: {agent.type}</div>
                        </div>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {agent.steps_count} steps
                        </span>
                      </div>

                      {/* Steps */}
                      {agent.steps.length > 0 && (
                        <div className="mt-3">
                          <div className="text-sm font-medium text-gray-700 mb-2">Steps:</div>
                          <div className="space-y-1">
                            {agent.steps.map((step, stepIndex) => (
                              <div
                                key={stepIndex}
                                className="flex items-center gap-2 text-sm text-gray-600"
                              >
                                <span className="text-blue-600">→</span>
                                <span>{step}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Routing */}
              {Object.keys(preview.routing).length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Routing</h3>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="space-y-2">
                      {Object.entries(preview.routing).map(([from, to]) => (
                        <div key={from} className="flex items-center gap-3 text-sm">
                          <span className="font-medium text-gray-900 bg-white px-3 py-1 rounded border">
                            {from}
                          </span>
                          <span className="text-blue-600">→</span>
                          <span className="font-medium text-gray-900 bg-white px-3 py-1 rounded border">
                            {to}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              No preview available
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 border-t flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
