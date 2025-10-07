/**
 * Agents Configuration Page
 * Manage agent settings for the current project
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useStore } from '../store/useStore';
import { AgentModelConfig } from '../components/AgentModelConfig';
import type { AgentsConfig, AgentConfig } from '../types/api';

export function AgentsPage() {
  const { currentProject } = useStore();
  const queryClient = useQueryClient();

  const projectName = currentProject?.name || 'default';

  // Fetch model registry
  const { data: modelRegistry, isLoading: isLoadingRegistry } = useQuery({
    queryKey: ['model-registry'],
    queryFn: () => api.getModelRegistry(),
  });

  // Fetch API keys
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

  const isLoading = isLoadingRegistry || isLoadingKeys || isLoadingConfig;

  if (isLoading) {
    return (
      <div className="p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Agents</h1>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!agentsConfig) {
    return (
      <div className="p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Agents</h1>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-center py-12">
            <p className="text-gray-500">No agents configuration found</p>
          </div>
        </div>
      </div>
    );
  }

  const agentEntries = Object.entries(agentsConfig.agents);
  const enabledCount = agentEntries.filter(([_, config]) => config.enabled).length;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Agents</h1>
        <p className="text-gray-600 mt-2">
          Configure agent settings for project: <span className="font-semibold">{projectName}</span>
        </p>
      </div>

      {/* Stats Card */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg shadow-lg p-6 mb-6 text-white">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <div className="text-sm opacity-90">Total Agents</div>
            <div className="text-3xl font-bold">{agentEntries.length}</div>
          </div>
          <div>
            <div className="text-sm opacity-90">Enabled</div>
            <div className="text-3xl font-bold">{enabledCount}</div>
          </div>
          <div>
            <div className="text-sm opacity-90">Disabled</div>
            <div className="text-3xl font-bold">{agentEntries.length - enabledCount}</div>
          </div>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <span className="text-2xl">ℹ️</span>
          <div className="text-sm text-blue-800">
            <p className="font-semibold mb-1">About Agents Configuration</p>
            <ul className="list-disc list-inside space-y-0.5 text-blue-700">
              <li>Each agent can use a specific model or inherit the project's default</li>
              <li>ReAct strategy controls how the agent reasons and acts</li>
              <li>Reflection allows agents to self-review their outputs</li>
              <li>Human-in-the-Loop requires approval for critical actions</li>
              <li>Network settings control where the agent server runs</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Agents List */}
      <div className="space-y-4">
        {agentEntries.map(([agentName, agentConfig]) => (
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
      </div>

      {/* Empty State */}
      {agentEntries.length === 0 && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <span className="text-6xl mb-4 block">🤖</span>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Agents Configured</h3>
          <p className="text-gray-600">
            Add agent configurations to your project's agents.json file
          </p>
        </div>
      )}
    </div>
  );
}
