/**
 * Prompts management page with tabs for System, Agents, and MCP prompts
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { PromptEditor } from '../components/PromptEditor';
import { useStore } from '../store/useStore';

type TabType = 'system' | 'agents' | 'mcp';

export function PromptsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('system');
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [selectedMCP, setSelectedMCP] = useState<string>('');
  const { currentProject } = useStore();

  const queryClient = useQueryClient();

  // Get current project name (default to 'default' for now)
  const projectName = currentProject?.name || 'default';

  // Fetch agents config to get list of agents
  const { data: agentsConfig } = useQuery({
    queryKey: ['agents', projectName],
    queryFn: () => api.getAgentsConfig(projectName),
  });

  // Fetch MCP config to get list of MCP servers
  const { data: mcpConfig } = useQuery({
    queryKey: ['mcp', projectName],
    queryFn: () => api.getMCPConfig(projectName),
  });

  // Fetch system prompt
  const { data: systemPrompt, isLoading: isLoadingSystem } = useQuery({
    queryKey: ['prompt', 'system', projectName],
    queryFn: () => api.getSystemPrompt(projectName),
    enabled: activeTab === 'system',
  });

  // Fetch agent prompt
  const { data: agentPrompt, isLoading: isLoadingAgent } = useQuery({
    queryKey: ['prompt', 'agent', projectName, selectedAgent],
    queryFn: () => api.getAgentPrompt(projectName, selectedAgent),
    enabled: activeTab === 'agents' && selectedAgent !== '',
  });

  // Fetch MCP prompt
  const { data: mcpPrompt, isLoading: isLoadingMCP } = useQuery({
    queryKey: ['prompt', 'mcp', projectName, selectedMCP],
    queryFn: () => api.getMCPPrompt(projectName, selectedMCP),
    enabled: activeTab === 'mcp' && selectedMCP !== '',
  });

  // Mutations
  const updateSystemMutation = useMutation({
    mutationFn: (content: string) => api.updateSystemPrompt(projectName, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompt', 'system', projectName] });
    },
  });

  const updateAgentMutation = useMutation({
    mutationFn: (content: string) => api.updateAgentPrompt(projectName, selectedAgent, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompt', 'agent', projectName, selectedAgent] });
    },
  });

  const updateMCPMutation = useMutation({
    mutationFn: (content: string) => api.updateMCPPrompt(projectName, selectedMCP, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompt', 'mcp', projectName, selectedMCP] });
    },
  });

  // State for editor
  const [editedContent, setEditedContent] = useState('');

  // Get current prompt content
  const getCurrentPrompt = () => {
    if (activeTab === 'system') return systemPrompt?.content || '';
    if (activeTab === 'agents') return agentPrompt?.content || '';
    if (activeTab === 'mcp') return mcpPrompt?.content || '';
    return '';
  };

  // Get agents list
  const agentsList = agentsConfig?.agents ? Object.keys(agentsConfig.agents) : [];

  // Get MCP servers list
  const mcpServersList = mcpConfig?.servers ? Object.keys(mcpConfig.servers) : [];

  // Set initial selected agent/MCP
  if (activeTab === 'agents' && selectedAgent === '' && agentsList.length > 0) {
    setSelectedAgent(agentsList[0]);
  }
  if (activeTab === 'mcp' && selectedMCP === '' && mcpServersList.length > 0) {
    setSelectedMCP(mcpServersList[0]);
  }

  const handleSave = () => {
    if (activeTab === 'system') {
      updateSystemMutation.mutate(editedContent);
    } else if (activeTab === 'agents') {
      updateAgentMutation.mutate(editedContent);
    } else if (activeTab === 'mcp') {
      updateMCPMutation.mutate(editedContent);
    }
  };

  const handleCancel = () => {
    setEditedContent(getCurrentPrompt());
  };

  const tabs: { id: TabType; label: string; icon: string }[] = [
    { id: 'system', label: 'System Prompt', icon: '⚙️' },
    { id: 'agents', label: 'Agent Prompts', icon: '🤖' },
    { id: 'mcp', label: 'MCP Prompts', icon: '🔌' },
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Prompts</h1>
        <p className="mt-2 text-gray-600">
          Manage system, agent, and MCP server prompts for project: <span className="font-semibold">{projectName}</span>
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <span className="text-lg">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg shadow p-6">
        {/* System Prompt Tab */}
        {activeTab === 'system' && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-900">System Prompt</h2>
              <p className="text-sm text-gray-600 mt-1">
                The main prompt that defines the AI assistant's behavior and personality.
              </p>
            </div>

            <PromptEditor
              value={getCurrentPrompt()}
              onChange={setEditedContent}
              onSave={handleSave}
              onCancel={handleCancel}
              isLoading={isLoadingSystem}
              isSaving={updateSystemMutation.isPending}
              placeholder="You are a helpful AI assistant specialized in multi-agent orchestration..."
            />
          </div>
        )}

        {/* Agent Prompts Tab */}
        {activeTab === 'agents' && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Agent Prompts</h2>
              <p className="text-sm text-gray-600 mt-1">
                Customize prompts for specific agents (researcher, analyst, writer, etc.)
              </p>
            </div>

            {agentsList.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No agents configured. Configure agents first.
              </div>
            ) : (
              <div>
                {/* Agent selector */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Agent
                  </label>
                  <select
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                    className="block w-full max-w-xs px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    {agentsList.map((agent) => (
                      <option key={agent} value={agent}>
                        {agent}
                      </option>
                    ))}
                  </select>
                </div>

                <PromptEditor
                  value={getCurrentPrompt()}
                  onChange={setEditedContent}
                  onSave={handleSave}
                  onCancel={handleCancel}
                  isLoading={isLoadingAgent}
                  isSaving={updateAgentMutation.isPending}
                  placeholder={`You are a ${selectedAgent} agent specialized in...`}
                />
              </div>
            )}
          </div>
        )}

        {/* MCP Prompts Tab */}
        {activeTab === 'mcp' && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-900">MCP Server Prompts</h2>
              <p className="text-sm text-gray-600 mt-1">
                Custom prompts for MCP servers to guide their tool usage.
              </p>
            </div>

            {mcpServersList.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No MCP servers configured. Configure MCP servers first.
              </div>
            ) : (
              <div>
                {/* MCP server selector */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select MCP Server
                  </label>
                  <select
                    value={selectedMCP}
                    onChange={(e) => setSelectedMCP(e.target.value)}
                    className="block w-full max-w-xs px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    {mcpServersList.map((server) => (
                      <option key={server} value={server}>
                        {server}
                      </option>
                    ))}
                  </select>
                </div>

                <PromptEditor
                  value={getCurrentPrompt()}
                  onChange={setEditedContent}
                  onSave={handleSave}
                  onCancel={handleCancel}
                  isLoading={isLoadingMCP}
                  isSaving={updateMCPMutation.isPending}
                  placeholder={`Instructions for using ${selectedMCP} MCP server tools...`}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
