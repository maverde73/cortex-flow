/**
 * Workflow list component with cards
 */

import type { WorkflowInfo } from '../types/api';

interface WorkflowListProps {
  workflows: WorkflowInfo[];
  onSelect: (workflow: WorkflowInfo) => void;
  onDelete: (workflowName: string) => void;
  selectedWorkflow?: string;
  isDeleting?: boolean;
}

export function WorkflowList({
  workflows,
  onSelect,
  onDelete,
  selectedWorkflow,
  isDeleting = false,
}: WorkflowListProps) {
  if (workflows.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-gray-600">
          <p className="text-lg font-medium mb-2">No workflows yet</p>
          <p className="text-sm">Create your first workflow to get started!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {workflows.map((workflow) => (
        <div
          key={workflow.name}
          className={`
            bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer border-2
            ${selectedWorkflow === workflow.name ? 'border-blue-500' : 'border-transparent'}
          `}
          onClick={() => onSelect(workflow)}
        >
          <div className="p-4">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">
                  {workflow.name}
                </h3>
                <p className="text-sm text-gray-500 mt-1">
                  v{workflow.version}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(workflow.name);
                }}
                disabled={isDeleting}
                className="text-gray-400 hover:text-red-600 transition-colors disabled:opacity-50"
                title="Delete workflow"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            </div>

            {/* Description */}
            <p className="text-sm text-gray-600 mb-3 line-clamp-2">
              {workflow.description || 'No description'}
            </p>

            {/* Agents */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-gray-500">Agents:</span>
              <div className="flex flex-wrap gap-1">
                {workflow.agents.length > 0 ? (
                  workflow.agents.slice(0, 3).map((agent) => (
                    <span
                      key={agent}
                      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {agent}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-gray-400">No agents</span>
                )}
                {workflow.agents.length > 3 && (
                  <span className="text-xs text-gray-500">
                    +{workflow.agents.length - 3}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
