/**
 * AgentModelConfig - Configuration card for a single agent
 * Allows editing model, ReAct strategy, temperature, and other settings
 */

import { useState } from 'react';
import { ModelSelector } from './ModelSelector';
import type { AgentConfig, ModelInfo, APIKeyConfig } from '../types/api';

interface AgentModelConfigProps {
  agentName: string;
  config: AgentConfig;
  models: ModelInfo[];
  apiKeys?: APIKeyConfig[];
  onUpdate: (agentName: string, config: AgentConfig) => void;
  isUpdating?: boolean;
}

const reactStrategies = [
  { value: 'fast', label: 'Fast', description: 'Quick responses, fewer iterations' },
  { value: 'balanced', label: 'Balanced', description: 'Good balance of speed and quality' },
  { value: 'deep', label: 'Deep', description: 'Thorough analysis, more iterations' },
  { value: 'creative', label: 'Creative', description: 'More exploration, higher temperature' },
];

export function AgentModelConfig({
  agentName,
  config,
  models,
  apiKeys = [],
  onUpdate,
  isUpdating = false,
}: AgentModelConfigProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localConfig, setLocalConfig] = useState(config);
  const [hasChanges, setHasChanges] = useState(false);

  const handleChange = (field: keyof AgentConfig, value: any) => {
    setLocalConfig({ ...localConfig, [field]: value });
    setHasChanges(true);
  };

  const handleSave = () => {
    onUpdate(agentName, localConfig);
    setHasChanges(false);
  };

  const handleReset = () => {
    setLocalConfig(config);
    setHasChanges(false);
  };

  // Agent icons
  const getAgentIcon = (name: string) => {
    if (name.includes('supervisor')) return '👔';
    if (name.includes('research')) return '🔍';
    if (name.includes('analyst')) return '📊';
    if (name.includes('writer')) return '✍️';
    if (name.includes('coder')) return '💻';
    if (name.includes('qa')) return '🧪';
    return '🤖';
  };

  return (
    <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">
      {/* Header */}
      <div
        className={`p-4 cursor-pointer transition-colors ${
          localConfig.enabled ? 'bg-blue-50 hover:bg-blue-100' : 'bg-gray-100 hover:bg-gray-200'
        }`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{getAgentIcon(agentName)}</span>
            <div>
              <h3 className="font-semibold text-gray-900">{agentName}</h3>
              <div className="text-sm text-gray-600 mt-0.5">
                {localConfig.model || 'Using default model'} •{' '}
                <span className="capitalize">{localConfig.react_strategy}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Enabled Toggle */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleChange('enabled', !localConfig.enabled);
                onUpdate(agentName, { ...localConfig, enabled: !localConfig.enabled });
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                localConfig.enabled ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  localConfig.enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>

            {/* Expand/Collapse Icon */}
            <svg
              className={`w-5 h-5 text-gray-500 transition-transform ${
                isExpanded ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* Expanded Configuration */}
      {isExpanded && (
        <div className="p-4 space-y-4 border-t border-gray-200">
          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
            <ModelSelector
              value={localConfig.model}
              onChange={(model) => handleChange('model', model)}
              models={models}
              apiKeys={apiKeys}
              placeholder="Use default model"
              showMetadata={true}
            />
            <div className="text-xs text-gray-500 mt-1">
              Leave empty to use the project's default model
            </div>
          </div>

          {/* ReAct Strategy */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ReAct Strategy</label>
            <select
              value={localConfig.react_strategy}
              onChange={(e) => handleChange('react_strategy', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              {reactStrategies.map((strategy) => (
                <option key={strategy.value} value={strategy.value}>
                  {strategy.label} - {strategy.description}
                </option>
              ))}
            </select>
          </div>

          {/* Temperature */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Temperature: {localConfig.temperature}
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={localConfig.temperature}
              onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Precise (0.0)</span>
              <span>Creative (2.0)</span>
            </div>
          </div>

          {/* Max Iterations */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Iterations</label>
            <input
              type="number"
              min="1"
              max="50"
              value={localConfig.max_iterations}
              onChange={(e) => handleChange('max_iterations', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Reflection Settings */}
          <div className="pt-3 border-t border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-medium text-gray-700">Enable Reflection</label>
              <button
                onClick={() => handleChange('enable_reflection', !localConfig.enable_reflection)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  localConfig.enable_reflection ? 'bg-blue-600' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    localConfig.enable_reflection ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {localConfig.enable_reflection && (
              <div className="space-y-3 pl-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reflection Threshold
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={localConfig.reflection_threshold}
                    onChange={(e) =>
                      handleChange('reflection_threshold', parseFloat(e.target.value))
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reflection Max Iterations
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={localConfig.reflection_max_iterations}
                    onChange={(e) =>
                      handleChange('reflection_max_iterations', parseInt(e.target.value))
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Human-in-the-Loop Settings */}
          <div className="pt-3 border-t border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-medium text-gray-700">
                Enable Human-in-the-Loop
              </label>
              <button
                onClick={() => handleChange('enable_hitl', !localConfig.enable_hitl)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  localConfig.enable_hitl ? 'bg-blue-600' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    localConfig.enable_hitl ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {localConfig.enable_hitl && (
              <div className="space-y-3 pl-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Require Approval For
                  </label>
                  <select
                    value={localConfig.hitl_require_approval_for}
                    onChange={(e) => handleChange('hitl_require_approval_for', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All actions</option>
                    <option value="tools">Tool calls only</option>
                    <option value="critical">Critical actions only</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Timeout (seconds)
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="600"
                    value={localConfig.hitl_timeout_seconds}
                    onChange={(e) =>
                      handleChange('hitl_timeout_seconds', parseInt(e.target.value))
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Network Configuration */}
          <div className="pt-3 border-t border-gray-200">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Host</label>
                <input
                  type="text"
                  value={localConfig.host}
                  onChange={(e) => handleChange('host', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
                <input
                  type="number"
                  min="1"
                  max="65535"
                  value={localConfig.port}
                  onChange={(e) => handleChange('port', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Save/Reset Buttons */}
          {hasChanges && (
            <div className="flex gap-2 pt-3 border-t border-gray-200">
              <button
                onClick={handleReset}
                disabled={isUpdating}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Reset
              </button>
              <button
                onClick={handleSave}
                disabled={isUpdating}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUpdating ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
