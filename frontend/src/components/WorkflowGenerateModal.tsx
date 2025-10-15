/**
 * Modal for AI-powered workflow generation
 */

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import type { Workflow } from '../types/api';

interface WorkflowGenerateModalProps {
  onClose: () => void;
  onAccept: (workflow: Workflow) => void;
}

export function WorkflowGenerateModal({
  onClose,
  onAccept,
}: WorkflowGenerateModalProps) {
  const [description, setDescription] = useState('');
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [selectedMCPs, setSelectedMCPs] = useState<string[]>([]);
  const [generatedWorkflow, setGeneratedWorkflow] = useState<Workflow | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const availableAgents = ['researcher', 'analyst', 'writer', 'reviewer'];
  const availableMCPs = ['brave-search', 'filesystem', 'sqlite', 'fetch'];

  const generateMutation = useMutation({
    mutationFn: async () => {
      const response = await api.generateWorkflow({
        description,
        agent_types: selectedAgents.length > 0 ? selectedAgents : undefined,
        mcp_servers: selectedMCPs.length > 0 ? selectedMCPs : undefined,
      });
      return response;
    },
    onSuccess: (data) => {
      setGeneratedWorkflow(data.workflow);
    },
  });

  const handleGenerate = () => {
    if (description.trim()) {
      generateMutation.mutate();
    }
  };

  const handleAccept = () => {
    if (generatedWorkflow) {
      onAccept(generatedWorkflow);
      onClose();
    }
  };

  const handleRegenerate = () => {
    setGeneratedWorkflow(null);
    generateMutation.mutate();
  };

  const toggleAgent = (agent: string) => {
    setSelectedAgents((prev) =>
      prev.includes(agent) ? prev.filter((a) => a !== agent) : [...prev, agent]
    );
  };

  const toggleMCP = (mcp: string) => {
    setSelectedMCPs((prev) =>
      prev.includes(mcp) ? prev.filter((m) => m !== mcp) : [...prev, mcp]
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4 border-b flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">✨ AI Workflow Generation</h2>
            <p className="text-blue-100 text-sm mt-1">
              Describe your task and let AI create the workflow
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 transition-colors"
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
        <div className="p-6 overflow-y-auto flex-1">
          {!generatedWorkflow ? (
            <div className="space-y-6">
              {/* Description Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Task Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Example: Create a workflow that researches a topic, analyzes the data, and generates a comprehensive report..."
                  className="w-full h-48 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y"
                  disabled={generateMutation.isPending}
                  maxLength={5000}
                />
                <p className="mt-2 text-sm text-gray-500">
                  {description.length}/5000 characters
                </p>
              </div>

              {/* Advanced Options Toggle */}
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
              >
                {showAdvanced ? '▼' : '▶'} Advanced Options (Optional)
              </button>

              {/* Advanced Options */}
              {showAdvanced && (
                <div className="space-y-4 bg-gray-50 p-4 rounded-lg border border-gray-200">
                  {/* Agent Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Preferred Agents (Optional)
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {availableAgents.map((agent) => (
                        <button
                          key={agent}
                          onClick={() => toggleAgent(agent)}
                          className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                            selectedAgents.includes(agent)
                              ? 'bg-blue-600 text-white'
                              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          {agent}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* MCP Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Required MCP Servers (Optional)
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {availableMCPs.map((mcp) => (
                        <button
                          key={mcp}
                          onClick={() => toggleMCP(mcp)}
                          className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                            selectedMCPs.includes(mcp)
                              ? 'bg-purple-600 text-white'
                              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          {mcp}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Error Display */}
              {generateMutation.isError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start gap-2">
                    <span className="text-red-600 font-bold">⚠️</span>
                    <div>
                      <div className="font-medium text-red-800">Generation Failed</div>
                      <div className="text-sm text-red-600 mt-1">
                        {generateMutation.error instanceof Error
                          ? generateMutation.error.message
                          : 'An error occurred while generating the workflow'}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {/* Success Message */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <span className="text-green-600 text-xl">✅</span>
                  <div>
                    <div className="font-medium text-green-800">Workflow Generated!</div>
                    <div className="text-sm text-green-600 mt-1">
                      Review the workflow below and accept to add it to your project
                    </div>
                  </div>
                </div>
              </div>

              {/* Workflow Preview */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <div className="text-sm text-gray-600">Workflow Name</div>
                    <div className="font-semibold text-gray-900">{generatedWorkflow.name}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Version</div>
                    <div className="font-semibold text-gray-900">{generatedWorkflow.version}</div>
                  </div>
                </div>

                <div className="mb-4">
                  <div className="text-sm text-gray-600 mb-1">Description</div>
                  <div className="text-gray-900">{generatedWorkflow.description}</div>
                </div>

                {/* Agents Summary */}
                {generatedWorkflow.agents && (
                  <div>
                    <div className="text-sm text-gray-600 mb-2">Agents</div>
                    <div className="flex flex-wrap gap-2">
                      {Object.keys(generatedWorkflow.agents).map((agentName) => (
                        <span
                          key={agentName}
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {agentName}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* JSON Preview (Collapsed) */}
              <details className="bg-white border border-gray-200 rounded-lg">
                <summary className="px-4 py-3 cursor-pointer text-sm font-medium text-gray-700 hover:bg-gray-50">
                  📄 View Full JSON
                </summary>
                <div className="px-4 py-3 border-t border-gray-200">
                  <pre className="text-xs text-gray-600 overflow-x-auto">
                    {JSON.stringify(generatedWorkflow, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 border-t flex justify-between items-center">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            disabled={generateMutation.isPending}
          >
            Cancel
          </button>

          <div className="flex gap-2">
            {generatedWorkflow ? (
              <>
                <button
                  onClick={handleRegenerate}
                  disabled={generateMutation.isPending}
                  className="px-4 py-2 text-sm font-medium text-blue-700 bg-white border border-blue-300 rounded-md hover:bg-blue-50 disabled:opacity-50"
                >
                  🔄 Regenerate
                </button>
                <button
                  onClick={handleAccept}
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700"
                >
                  ✓ Accept & Save
                </button>
              </>
            ) : (
              <button
                onClick={handleGenerate}
                disabled={!description.trim() || generateMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generateMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <svg
                      className="animate-spin h-4 w-4"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Generating...
                  </span>
                ) : (
                  '✨ Generate Workflow'
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
