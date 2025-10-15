/**
 * Dashboard page with project overview
 */

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { useStore } from '../store/useStore';

export function DashboardPage() {
  const { currentProject } = useStore();
  const projectName = currentProject?.name || 'default';

  // Fetch all data
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.listProjects(),
  });

  const { data: workflows } = useQuery({
    queryKey: ['workflows', projectName],
    queryFn: () => api.listWorkflows(projectName),
  });

  const { data: agentsConfig } = useQuery({
    queryKey: ['agents-config', projectName],
    queryFn: () => api.getAgentsConfig(projectName),
  });

  const { data: mcpConfig } = useQuery({
    queryKey: ['mcp-config', projectName],
    queryFn: () => api.getMCPConfig(projectName),
  });

  const { data: promptsInfo } = useQuery({
    queryKey: ['prompts-info', projectName],
    queryFn: () => api.listPrompts(projectName),
  });

  const projectsCount = projects?.length || 0;
  const workflowsCount = workflows?.length || 0;
  const agentsCount = Object.keys(agentsConfig?.agents || {}).length;
  const mcpServersCount = Object.keys(mcpConfig?.servers || {}).length;
  const promptsCount =
    (promptsInfo?.system ? 1 : 0) +
    Object.keys(promptsInfo?.agents || {}).length +
    Object.keys(promptsInfo?.mcp || {}).length;

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Overview of project: <span className="font-semibold">{currentProject?.name || 'default'}</span>
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <Link
          to="/projects"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-medium text-gray-500">Projects</div>
            <div className="text-2xl">📁</div>
          </div>
          <div className="text-3xl font-bold text-gray-900">{projectsCount}</div>
          <div className="mt-2 text-xs text-gray-500">Click to manage</div>
        </Link>

        <Link
          to="/workflows"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-medium text-gray-500">Workflows</div>
            <div className="text-2xl">🔄</div>
          </div>
          <div className="text-3xl font-bold text-gray-900">{workflowsCount}</div>
          <div className="mt-2 text-xs text-gray-500">Click to manage</div>
        </Link>

        <Link
          to="/agents"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-medium text-gray-500">Agents</div>
            <div className="text-2xl">🤖</div>
          </div>
          <div className="text-3xl font-bold text-gray-900">{agentsCount}</div>
          <div className="mt-2 text-xs text-gray-500">Click to configure</div>
        </Link>

        <Link
          to="/mcp"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-medium text-gray-500">MCP Servers</div>
            <div className="text-2xl">🔌</div>
          </div>
          <div className="text-3xl font-bold text-gray-900">{mcpServersCount}</div>
          <div className="mt-2 text-xs text-gray-500">Click to configure</div>
        </Link>

        <Link
          to="/prompts"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-medium text-gray-500">Prompts</div>
            <div className="text-2xl">💬</div>
          </div>
          <div className="text-3xl font-bold text-gray-900">{promptsCount}</div>
          <div className="mt-2 text-xs text-gray-500">Click to edit</div>
        </Link>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg p-6 text-white">
          <h2 className="text-xl font-bold mb-2">✨ Create Workflow</h2>
          <p className="text-blue-100 mb-4">Generate a new workflow using AI</p>
          <Link
            to="/workflows"
            className="inline-block px-4 py-2 bg-white text-blue-600 rounded-md font-medium hover:bg-blue-50 transition-colors"
          >
            Go to Workflows
          </Link>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-lg p-6 text-white">
          <h2 className="text-xl font-bold mb-2">🔌 Add MCP Server</h2>
          <p className="text-purple-100 mb-4">Browse and add MCP servers from registry</p>
          <Link
            to="/mcp"
            className="inline-block px-4 py-2 bg-white text-purple-600 rounded-md font-medium hover:bg-purple-50 transition-colors"
          >
            Browse Registry
          </Link>
        </div>
      </div>

      {/* Project Info */}
      {currentProject && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Current Project</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-sm font-medium text-gray-500">Name</div>
              <div className="mt-1 text-gray-900">{currentProject.name}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Description</div>
              <div className="mt-1 text-gray-900">{currentProject.description || 'No description'}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Status</div>
              <div className="mt-1">
                {currentProject.active ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Active
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    Inactive
                  </span>
                )}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Created</div>
              <div className="mt-1 text-gray-900">
                {currentProject.created_at
                  ? new Date(currentProject.created_at).toLocaleDateString()
                  : 'Unknown'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Getting Started */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Welcome to Cortex Flow Editor</h2>
        <p className="text-gray-600 mb-4">
          Cortex Flow is a powerful multi-agent AI workflow system. Use this editor to:
        </p>
        <ul className="space-y-2 text-gray-600">
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-1">✓</span>
            <span><strong>Create Workflows:</strong> Design complex AI workflows with multiple agents</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-1">✓</span>
            <span><strong>Configure Agents:</strong> Set up specialized AI agents for different tasks</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-1">✓</span>
            <span><strong>Manage Prompts:</strong> Customize system and agent prompts</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-1">✓</span>
            <span><strong>Integrate MCP Servers:</strong> Connect external tools and data sources</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-1">✓</span>
            <span><strong>Visual Editing:</strong> Use both code and visual editors for workflows</span>
          </li>
        </ul>

        <div className="mt-6 pt-6 border-t">
          <h3 className="font-semibold text-gray-900 mb-2">Quick Links</h3>
          <div className="flex flex-wrap gap-2">
            <Link to="/projects" className="text-sm text-blue-600 hover:text-blue-700 hover:underline">
              Projects
            </Link>
            <span className="text-gray-300">•</span>
            <Link to="/workflows" className="text-sm text-blue-600 hover:text-blue-700 hover:underline">
              Workflows
            </Link>
            <span className="text-gray-300">•</span>
            <Link to="/agents" className="text-sm text-blue-600 hover:text-blue-700 hover:underline">
              Agents
            </Link>
            <span className="text-gray-300">•</span>
            <Link to="/prompts" className="text-sm text-blue-600 hover:text-blue-700 hover:underline">
              Prompts
            </Link>
            <span className="text-gray-300">•</span>
            <Link to="/mcp" className="text-sm text-blue-600 hover:text-blue-700 hover:underline">
              MCP Servers
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
