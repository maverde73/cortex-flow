/**
 * MCP (Model Context Protocol) management page
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useStore } from '../store/useStore';
import { MCPBrowser } from '../components/MCPBrowser';
import { MCPServerConfig } from '../components/MCPServerConfig';
import { MCPServerCreate } from '../components/MCPServerCreate';

type ViewMode = 'installed' | 'browse';

export function MCPPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('installed');
  const [showCreateForm, setShowCreateForm] = useState(false);

  const { currentProject } = useStore();
  const queryClient = useQueryClient();

  const projectName = currentProject?.name || 'default';

  // Fetch MCP registry
  const { data: registry } = useQuery({
    queryKey: ['mcp-registry'],
    queryFn: () => api.browseMCPRegistry(),
  });

  // Fetch project MCP config
  const { data: mcpConfig, isLoading: isLoadingConfig } = useQuery({
    queryKey: ['mcp-config', projectName],
    queryFn: () => api.getMCPConfig(projectName),
  });

  // Update MCP config mutation
  const updateConfigMutation = useMutation({
    mutationFn: (config: any) => api.updateMCPConfig(projectName, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-config', projectName] });
    },
  });


  // Handlers
  const handleAddServer = (serverId: string) => {
    if (!mcpConfig) return;

    const newConfig = {
      ...mcpConfig,
      servers: {
        ...mcpConfig.servers,
        [serverId]: {
          type: 'remote',
          transport: 'streamable_http',
          url: '',
          api_key: null,
          local_path: null,
          command: null,  // Required by backend even for remote servers
          enabled: true,
          timeout: 30.0,
        },
      },
    };

    updateConfigMutation.mutate(newConfig);
    setViewMode('installed');
  };

  const handleUpdateServer = async (serverId: string, serverConfig: any) => {
    if (!mcpConfig) return;

    const newConfig = {
      ...mcpConfig,
      servers: {
        ...mcpConfig.servers,
        [serverId]: serverConfig,
      },
    };

    // Save configuration first
    updateConfigMutation.mutate(newConfig, {
      onSuccess: async () => {
        // Auto-test the server after successful save
        try {
          console.log(`Auto-testing MCP server '${serverId}' after save...`);
          const result = await api.autoTestMCPServer(projectName, serverId, serverConfig);

          if (result.success) {
            console.log(`✅ Auto-test successful for '${serverId}':`, result.server_config?.status);
            // Refresh MCP config to show updated status
            queryClient.invalidateQueries({ queryKey: ['mcp-config', projectName] });
          } else {
            console.warn(`⚠️ Auto-test failed for '${serverId}':`, result.error);
          }
        } catch (error) {
          console.error(`❌ Auto-test error for '${serverId}':`, error);
        }
      }
    });
  };

  const handleRemoveServer = (serverId: string) => {
    if (!mcpConfig) return;
    if (!confirm(`Remove MCP server "${serverId}"?`)) return;

    const { [serverId]: removed, ...remainingServers } = mcpConfig.servers;
    const newConfig = {
      ...mcpConfig,
      servers: remainingServers,
    };

    updateConfigMutation.mutate(newConfig);
  };

  const handleCreateServer = async (serverName: string, serverConfig: any) => {
    if (!mcpConfig) return;

    // Check if server name already exists
    if (mcpConfig.servers[serverName]) {
      alert(`❌ Server "${serverName}" already exists. Please choose a different name.`);
      return;
    }

    const newConfig = {
      ...mcpConfig,
      servers: {
        ...mcpConfig.servers,
        [serverName]: serverConfig,
      },
    };

    // Save configuration first
    updateConfigMutation.mutate(newConfig, {
      onSuccess: async () => {
        setShowCreateForm(false);

        // Auto-test the new server after successful creation
        try {
          console.log(`Auto-testing new MCP server '${serverName}'...`);
          const result = await api.autoTestMCPServer(projectName, serverName, serverConfig);

          if (result.success) {
            console.log(`✅ Auto-test successful for '${serverName}':`, result.server_config?.status);
            // Refresh MCP config to show updated status
            queryClient.invalidateQueries({ queryKey: ['mcp-config', projectName] });
          } else {
            console.warn(`⚠️ Auto-test failed for '${serverName}':`, result.error);
          }
        } catch (error) {
          console.error(`❌ Auto-test error for '${serverName}':`, error);
        }
      }
    });
  };

  const installedServers = Object.keys(mcpConfig?.servers || {});

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">MCP Servers</h1>
        <p className="mt-2 text-gray-600">
          Manage Model Context Protocol servers for project:{' '}
          <span className="font-semibold">{projectName}</span>
        </p>
      </div>

      {/* View Mode Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <div className="flex gap-4">
          <button
            onClick={() => setViewMode('installed')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              viewMode === 'installed'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Installed Servers ({installedServers.length})
          </button>
          <button
            onClick={() => setViewMode('browse')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              viewMode === 'browse'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Browse Registry
          </button>
        </div>
      </div>

      {/* Content */}
      {isLoadingConfig ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-gray-600">Loading MCP configuration...</div>
        </div>
      ) : (
        <>
          {viewMode === 'installed' && (
            <div className="space-y-4">
              {/* Add Server Button */}
              {!showCreateForm && (
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="w-full px-4 py-3 text-sm font-medium text-blue-600 bg-blue-50 border-2 border-dashed border-blue-300 rounded-lg hover:bg-blue-100 hover:border-blue-400 transition-colors flex items-center justify-center gap-2"
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
                      d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                    />
                  </svg>
                  Add New MCP Server
                </button>
              )}

              {/* Create Form */}
              {showCreateForm && (
                <MCPServerCreate
                  onCreate={handleCreateServer}
                  onCancel={() => setShowCreateForm(false)}
                />
              )}

              {/* Installed Servers */}
              {installedServers.length === 0 && !showCreateForm ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                  <svg
                    className="w-16 h-16 mx-auto mb-4 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                    />
                  </svg>
                  <p className="text-gray-600 mb-4">No MCP servers installed yet</p>
                  <button
                    onClick={() => setViewMode('browse')}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                  >
                    Browse Registry
                  </button>
                </div>
              ) : (
                installedServers.map((serverId) => (
                  <MCPServerConfig
                    key={serverId}
                    serverId={serverId}
                    serverName={serverId}
                    config={mcpConfig!.servers[serverId]}
                    onUpdate={handleUpdateServer}
                    onRemove={handleRemoveServer}
                  />
                ))
              )}
            </div>
          )}

          {viewMode === 'browse' && (
            <MCPBrowser
              servers={registry?.servers || []}
              onAddServer={handleAddServer}
              installedServers={installedServers}
            />
          )}
        </>
      )}
    </div>
  );
}
