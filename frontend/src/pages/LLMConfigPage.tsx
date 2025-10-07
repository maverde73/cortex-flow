/**
 * LLM Configuration Page
 * Manage models and agent configurations
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useStore } from '../store/useStore';
import { AgentModelConfig } from '../components/AgentModelConfig';
import { ModelSelector } from '../components/ModelSelector';
import { APIKeyManager } from '../components/APIKeyManager';
import type { AgentsConfig, AgentConfig, ProviderType } from '../types/api';

type ViewMode = 'agents' | 'providers' | 'global';

export function LLMConfigPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('global');
  const { currentProject } = useStore();
  const queryClient = useQueryClient();

  const projectName = currentProject?.name || 'default';

  // Fetch model registry
  const { data: modelRegistry, isLoading: isLoadingRegistry } = useQuery({
    queryKey: ['model-registry'],
    queryFn: () => api.getModelRegistry(),
  });

  // Fetch API keys (full config with masked values)
  const { data: apiKeys, isLoading: isLoadingKeys } = useQuery({
    queryKey: ['api-keys'],
    queryFn: () => api.getAPIKeys(),
  });

  // Fetch agents config
  const { data: agentsConfig, isLoading: isLoadingConfig } = useQuery({
    queryKey: ['agents-config', projectName],
    queryFn: () => api.getAgentsConfig(projectName),
  });

  // Update agents config mutation
  const updateConfigMutation = useMutation({
    mutationFn: (config: AgentsConfig) => api.updateAgentsConfig(projectName, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents-config', projectName] });
    },
  });

  // Get all models as flat array
  const allModels = modelRegistry
    ? Object.values(modelRegistry.providers).flat()
    : [];

  // Handle default model change
  const handleDefaultModelChange = (modelId: string) => {
    if (!agentsConfig) return;

    const newConfig: AgentsConfig = {
      ...agentsConfig,
      default_model: modelId,
    };

    updateConfigMutation.mutate(newConfig);
  };

  // Handle fallback order change
  const handleFallbackOrderChange = (order: string) => {
    if (!agentsConfig) return;

    const newConfig: AgentsConfig = {
      ...agentsConfig,
      provider_fallback_order: order,
    };

    updateConfigMutation.mutate(newConfig);
  };

  // Handle web app model change
  const handleWebAppModelChange = (modelId: string) => {
    if (!agentsConfig) return;

    const newConfig: AgentsConfig = {
      ...agentsConfig,
      web_app_model: modelId || undefined,  // Remove field if empty
    };

    updateConfigMutation.mutate(newConfig);
  };

  // Handle agent config update
  const handleAgentUpdate = (agentName: string, agentConfig: AgentConfig) => {
    if (!agentsConfig) return;

    const newConfig: AgentsConfig = {
      ...agentsConfig,
      agents: {
        ...agentsConfig.agents,
        [agentName]: agentConfig,
      },
    };

    updateConfigMutation.mutate(newConfig);
  };

  // Provider colors
  const getProviderColor = (provider: ProviderType) => {
    switch (provider) {
      case 'openai':
        return 'bg-green-500';
      case 'anthropic':
        return 'bg-orange-500';
      case 'google':
        return 'bg-blue-500';
      case 'groq':
        return 'bg-purple-500';
      case 'openrouter':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const isLoading = isLoadingRegistry || isLoadingKeys || isLoadingConfig;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">LLM Configuration</h1>
        <p className="mt-2 text-gray-600">
          Configure language models and agent settings for project:{' '}
          <span className="font-semibold">{projectName}</span>
        </p>
      </div>

      {/* View Mode Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <div className="flex gap-4">
          <button
            onClick={() => setViewMode('global')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              viewMode === 'global'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            🌐 Global Settings
          </button>
          <button
            onClick={() => setViewMode('agents')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              viewMode === 'agents'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            🤖 Agent Configuration ({Object.keys(agentsConfig?.agents || {}).length})
          </button>
          <button
            onClick={() => setViewMode('providers')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              viewMode === 'providers'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            🔑 API Providers
          </button>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-gray-600">Loading configuration...</div>
        </div>
      ) : (
        <>
          {/* Global Settings View */}
          {viewMode === 'global' && agentsConfig && (
            <div className="space-y-6">
              {/* Default Model */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Default Model</h2>
                <p className="text-sm text-gray-600 mb-4">
                  This model will be used for all agents unless overridden in individual agent
                  configurations.
                </p>
                <ModelSelector
                  value={agentsConfig.default_model}
                  onChange={handleDefaultModelChange}
                  models={allModels}
                  apiKeys={apiKeys}
                  placeholder="Select default model..."
                  showMetadata={true}
                />
              </div>

              {/* Web App Model */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Web App Model ✨
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                  This model will be used for web application AI features (workflow generation, conversions).
                  If not set, defaults to the Default Model above.
                </p>
                <ModelSelector
                  value={agentsConfig.web_app_model || ''}
                  onChange={handleWebAppModelChange}
                  models={allModels}
                  apiKeys={apiKeys}
                  placeholder="Use default model (or select a different one)..."
                  showMetadata={true}
                />
                <div className="mt-3 bg-purple-50 border border-purple-200 rounded p-3">
                  <div className="text-xs text-purple-700">
                    <span className="font-semibold">Used for:</span>
                    <ul className="list-disc list-inside ml-2 mt-1 space-y-0.5">
                      <li>AI-powered workflow generation (Generate with AI)</li>
                      <li>Workflow ↔ natural language conversions</li>
                      <li>Prompt optimization and analysis</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Provider Fallback Order */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Provider Fallback Order
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                  If the primary provider is unavailable, the system will automatically fall back
                  to these providers in order.
                </p>
                <input
                  type="text"
                  value={agentsConfig.provider_fallback_order}
                  onChange={(e) => handleFallbackOrderChange(e.target.value)}
                  placeholder="openai,anthropic,google,groq,openrouter"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
                <div className="text-xs text-gray-500 mt-2">
                  Comma-separated list of providers. Example: openai,anthropic,google
                </div>
              </div>

              {/* Info Panel */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 text-xl">ℹ️</span>
                  <div className="flex-1">
                    <div className="font-medium text-blue-800">Model Selection Hierarchy</div>
                    <div className="text-sm text-blue-600 mt-1">
                      <ol className="list-decimal list-inside space-y-1">
                        <li>Agent-specific model (if configured in Agent Configuration)</li>
                        <li>Project default model (configured above)</li>
                        <li>System default with provider fallback</li>
                      </ol>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Agents Configuration View */}
          {viewMode === 'agents' && agentsConfig && (
            <div className="space-y-4">
              {Object.entries(agentsConfig.agents).map(([agentName, agentConfig]) => (
                <AgentModelConfig
                  key={agentName}
                  agentName={agentName}
                  config={agentConfig}
                  models={allModels}
                  apiKeys={apiKeys}
                  onUpdate={handleAgentUpdate}
                  isUpdating={updateConfigMutation.isPending}
                />
              ))}

              {Object.keys(agentsConfig.agents).length === 0 && (
                <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                  <span className="text-4xl mb-4 block">🤖</span>
                  <p className="text-gray-600">No agents configured yet</p>
                </div>
              )}
            </div>
          )}

          {/* Providers View */}
          {viewMode === 'providers' && apiKeys && modelRegistry && (
            <div className="space-y-6">
              {/* API Key Management */}
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Manage API Keys
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                  Configure your API keys for each LLM provider. Keys are stored securely in your .env file.
                </p>
                <APIKeyManager apiKeys={apiKeys} isLoading={isLoadingKeys} />
              </div>

              {/* Available Models by Provider */}
              <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 text-white">
                  <h2 className="text-lg font-bold">Available Models</h2>
                  <p className="text-sm text-blue-100 mt-1">
                    {allModels.length} models across {Object.keys(modelRegistry.providers).length} providers
                  </p>
                </div>

                <div className="p-4 space-y-4">
                  {Object.entries(modelRegistry.providers).map(([provider, models]) => (
                    <div key={provider}>
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-2 h-2 rounded-full ${getProviderColor(provider as ProviderType)}`} />
                        <h3 className="font-semibold text-gray-900 capitalize">{provider}</h3>
                        <span className="text-sm text-gray-500">({models.length} models)</span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 ml-4">
                        {models.map((model) => (
                          <div
                            key={model.model_id}
                            className="p-2 bg-gray-50 rounded border border-gray-200 text-sm"
                          >
                            <div className="font-medium text-gray-900">{model.display_name}</div>
                            <div className="text-xs text-gray-500 mt-1">
                              {model.context_window.toLocaleString()} tokens •{' '}
                              <span className="capitalize">{model.cost_tier}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
