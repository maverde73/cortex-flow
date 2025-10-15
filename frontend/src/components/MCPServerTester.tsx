/**
 * MCPServerTester - Comprehensive testing interface for MCP servers
 *
 * Provides a tabbed interface to test all MCP protocol capabilities:
 * - Connection & Capabilities
 * - Resources (list, read, templates)
 * - Tools (list, call)
 * - Prompts (list, get)
 * - Completions
 * - Session Management
 */

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import type {
  MCPConnectionData,
  MCPResourcesListData,
  MCPResourceReadData,
  MCPResourceTemplatesData,
  MCPToolsListData,
  MCPToolCallResult,
  MCPPromptsListData,
  MCPPromptGetData,
  MCPCompletionsData,
} from '../types/api';

interface MCPServerTesterProps {
  serverId: string;
  serverName: string;
  serverConfig: Record<string, any>;
  projectName: string;
  onClose?: () => void;
}

type TabType = 'connection' | 'resources' | 'tools' | 'prompts' | 'completions' | 'session';

export function MCPServerTester({
  serverName,
  serverConfig,
  projectName,
  onClose,
}: MCPServerTesterProps) {
  const [activeTab, setActiveTab] = useState<TabType>('connection');
  const [connectionData, setConnectionData] = useState<MCPConnectionData | null>(null);

  // Resources state
  const [resourcesList, setResourcesList] = useState<MCPResourcesListData | null>(null);
  const [resourceContent, setResourceContent] = useState<MCPResourceReadData | null>(null);
  const [resourceTemplates, setResourceTemplates] = useState<MCPResourceTemplatesData | null>(null);

  // Tools state
  const [toolsList, setToolsList] = useState<MCPToolsListData | null>(null);
  const [selectedTool, setSelectedTool] = useState<string>('');
  const [toolArguments, setToolArguments] = useState<string>('{}');
  const [toolResult, setToolResult] = useState<MCPToolCallResult | null>(null);

  // Prompts state
  const [promptsList, setPromptsList] = useState<MCPPromptsListData | null>(null);
  const [selectedPrompt, setSelectedPrompt] = useState<string>('');
  const [promptArguments, setPromptArguments] = useState<string>('{}');
  const [promptContent, setPromptContent] = useState<MCPPromptGetData | null>(null);

  // Completions state
  const [completionsRef, setCompletionsRef] = useState<string>('{"type":"ref/resource","uri":""}');
  const [completionsArg, setCompletionsArg] = useState<string>('{"name":"path","value":""}');
  const [completionsResult, setCompletionsResult] = useState<MCPCompletionsData | null>(null);

  // Generic result display for errors
  const [lastError, setLastError] = useState<string | null>(null);

  // Connection mutation
  const connectionMutation = useMutation({
    mutationFn: () => api.testMCPConnectionAndCapabilities(projectName, serverName, serverConfig),
    onSuccess: (result) => {
      if (result.success && result.data) {
        setConnectionData(result.data);
        setLastError(null);
      } else {
        setLastError(result.error || 'Connection failed');
      }
    },
    onError: (error: any) => {
      setLastError(error.response?.data?.error || error.message || 'Connection failed');
    },
  });

  // Resources mutations
  const resourcesListMutation = useMutation({
    mutationFn: () => api.testMCPResourcesList(projectName, serverName, serverConfig),
    onSuccess: (result) => {
      if (result.success && result.data) {
        setResourcesList(result.data);
        setLastError(null);
      } else {
        setLastError(result.error || 'Failed to list resources');
      }
    },
  });

  const resourceReadMutation = useMutation({
    mutationFn: (uri: string) => api.testMCPResourceRead(projectName, serverName, serverConfig, uri),
    onSuccess: (result) => {
      if (result.success && result.data) {
        setResourceContent(result.data);
        setLastError(null);
      } else {
        setLastError(result.error || 'Failed to read resource');
      }
    },
  });

  const resourceTemplatesMutation = useMutation({
    mutationFn: () => api.testMCPResourceTemplates(projectName, serverName, serverConfig),
    onSuccess: (result) => {
      if (result.success && result.data) {
        setResourceTemplates(result.data);
        setLastError(null);
      } else {
        setLastError(result.error || 'Failed to list resource templates');
      }
    },
  });

  // Tools mutations
  const toolsListMutation = useMutation({
    mutationFn: () => api.testMCPToolsList(projectName, serverName, serverConfig),
    onSuccess: (result) => {
      if (result.success && result.data) {
        setToolsList(result.data);
        setLastError(null);
      } else {
        setLastError(result.error || 'Failed to list tools');
      }
    },
  });

  const toolCallMutation = useMutation({
    mutationFn: ({ tool, args }: { tool: string; args: Record<string, any> }) =>
      api.testMCPToolCall(projectName, serverName, serverConfig, tool, args),
    onSuccess: (result) => {
      if (result.success && result.data) {
        setToolResult(result.data);
        setLastError(null);
      } else {
        setLastError(result.error || 'Tool call failed');
      }
    },
  });

  // Prompts mutations
  const promptsListMutation = useMutation({
    mutationFn: () => api.testMCPPromptsList(projectName, serverName, serverConfig),
    onSuccess: (result) => {
      if (result.success && result.data) {
        setPromptsList(result.data);
        setLastError(null);
      } else {
        setLastError(result.error || 'Failed to list prompts');
      }
    },
  });

  const promptGetMutation = useMutation({
    mutationFn: ({ prompt, args }: { prompt: string; args?: Record<string, string> }) =>
      api.testMCPPromptGet(projectName, serverName, serverConfig, prompt, args),
    onSuccess: (result) => {
      if (result.success && result.data) {
        setPromptContent(result.data);
        setLastError(null);
      } else {
        setLastError(result.error || 'Failed to get prompt');
      }
    },
  });

  // Completions mutation
  const completionsMutation = useMutation({
    mutationFn: ({ ref, arg }: { ref: Record<string, any>; arg: Record<string, string> }) =>
      api.testMCPCompletions(projectName, serverName, serverConfig, ref, arg),
    onSuccess: (result) => {
      if (result.success && result.data) {
        setCompletionsResult(result.data);
        setLastError(null);
      } else {
        setLastError(result.error || 'Completions failed');
      }
    },
  });

  // Session reset mutation
  const sessionResetMutation = useMutation({
    mutationFn: () => api.testMCPSessionReset(projectName, serverName, serverConfig),
    onSuccess: (result) => {
      if (result.success && result.data) {
        setConnectionData(result.data);
        setLastError(null);
        alert('✅ Session reset successfully');
      } else {
        setLastError(result.error || 'Session reset failed');
      }
    },
  });

  // Tab configuration
  const tabs: { id: TabType; label: string }[] = [
    { id: 'connection', label: 'Connection' },
    { id: 'resources', label: 'Resources' },
    { id: 'tools', label: 'Tools' },
    { id: 'prompts', label: 'Prompts' },
    { id: 'completions', label: 'Completions' },
    { id: 'session', label: 'Session' },
  ];

  const renderConnectionTab = () => (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button
          onClick={() => connectionMutation.mutate()}
          disabled={connectionMutation.isPending}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {connectionMutation.isPending ? 'Testing...' : 'Test Connection'}
        </button>
      </div>

      {connectionData && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Server Info</h4>
          <pre className="text-xs overflow-auto">
            {JSON.stringify(connectionData, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );

  const renderResourcesTab = () => (
    <div className="space-y-4">
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => resourcesListMutation.mutate()}
          disabled={resourcesListMutation.isPending}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {resourcesListMutation.isPending ? 'Loading...' : 'List Resources'}
        </button>
        <button
          onClick={() => resourceTemplatesMutation.mutate()}
          disabled={resourceTemplatesMutation.isPending}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {resourceTemplatesMutation.isPending ? 'Loading...' : 'List Templates'}
        </button>
      </div>

      {resourcesList && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Resources ({resourcesList.resources.length})</h4>
          <div className="space-y-2">
            {resourcesList.resources.map((resource) => (
              <div key={resource.uri} className="p-2 bg-white rounded border">
                <div className="font-medium text-sm">{resource.name}</div>
                <div className="text-xs text-gray-500">{resource.uri}</div>
                {resource.description && (
                  <div className="text-xs text-gray-600 mt-1">{resource.description}</div>
                )}
                <button
                  onClick={() => resourceReadMutation.mutate(resource.uri)}
                  className="mt-2 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                >
                  Read
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {resourceContent && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Resource Content</h4>
          <pre className="text-xs overflow-auto max-h-96">
            {JSON.stringify(resourceContent, null, 2)}
          </pre>
        </div>
      )}

      {resourceTemplates && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Resource Templates ({resourceTemplates.resourceTemplates.length})</h4>
          <pre className="text-xs overflow-auto">
            {JSON.stringify(resourceTemplates, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );

  const renderToolsTab = () => (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button
          onClick={() => toolsListMutation.mutate()}
          disabled={toolsListMutation.isPending}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {toolsListMutation.isPending ? 'Loading...' : 'List Tools'}
        </button>
      </div>

      {toolsList && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Tools ({toolsList.tools.length})</h4>
          <div className="space-y-2">
            {toolsList.tools.map((tool) => (
              <div key={tool.name} className="p-2 bg-white rounded border">
                <div className="font-medium text-sm">{tool.name}</div>
                {tool.description && (
                  <div className="text-xs text-gray-600 mt-1">{tool.description}</div>
                )}
                <details className="mt-2 text-xs">
                  <summary className="cursor-pointer text-blue-600">Input Schema</summary>
                  <pre className="mt-1 p-2 bg-gray-50 rounded overflow-auto">
                    {JSON.stringify(tool.inputSchema, null, 2)}
                  </pre>
                </details>
                <button
                  onClick={() => setSelectedTool(tool.name)}
                  className="mt-2 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                >
                  Call Tool
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedTool && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Call Tool: {selectedTool}</h4>
          <label className="block text-sm mb-2">
            Arguments (JSON):
            <textarea
              value={toolArguments}
              onChange={(e) => setToolArguments(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
              rows={4}
            />
          </label>
          <button
            onClick={() => {
              try {
                const args = JSON.parse(toolArguments);
                toolCallMutation.mutate({ tool: selectedTool, args });
              } catch (e) {
                setLastError('Invalid JSON in arguments');
              }
            }}
            disabled={toolCallMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {toolCallMutation.isPending ? 'Calling...' : 'Execute'}
          </button>
        </div>
      )}

      {toolResult && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Tool Result</h4>
          <pre className="text-xs overflow-auto max-h-96">
            {JSON.stringify(toolResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );

  const renderPromptsTab = () => (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button
          onClick={() => promptsListMutation.mutate()}
          disabled={promptsListMutation.isPending}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {promptsListMutation.isPending ? 'Loading...' : 'List Prompts'}
        </button>
      </div>

      {promptsList && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Prompts ({promptsList.prompts.length})</h4>
          <div className="space-y-2">
            {promptsList.prompts.map((prompt) => (
              <div key={prompt.name} className="p-2 bg-white rounded border">
                <div className="font-medium text-sm">{prompt.name}</div>
                {prompt.description && (
                  <div className="text-xs text-gray-600 mt-1">{prompt.description}</div>
                )}
                {prompt.arguments && prompt.arguments.length > 0 && (
                  <details className="mt-2 text-xs">
                    <summary className="cursor-pointer text-blue-600">Arguments</summary>
                    <ul className="mt-1 ml-4 list-disc">
                      {prompt.arguments.map((arg) => (
                        <li key={arg.name}>
                          <span className="font-medium">{arg.name}</span>
                          {arg.required && <span className="text-red-600">*</span>}
                          {arg.description && `: ${arg.description}`}
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
                <button
                  onClick={() => setSelectedPrompt(prompt.name)}
                  className="mt-2 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                >
                  Get Prompt
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedPrompt && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Get Prompt: {selectedPrompt}</h4>
          <label className="block text-sm mb-2">
            Arguments (JSON, optional):
            <textarea
              value={promptArguments}
              onChange={(e) => setPromptArguments(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
              rows={3}
            />
          </label>
          <button
            onClick={() => {
              try {
                const args = promptArguments.trim() ? JSON.parse(promptArguments) : undefined;
                promptGetMutation.mutate({ prompt: selectedPrompt, args });
              } catch (e) {
                setLastError('Invalid JSON in arguments');
              }
            }}
            disabled={promptGetMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {promptGetMutation.isPending ? 'Loading...' : 'Get Prompt'}
          </button>
        </div>
      )}

      {promptContent && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Prompt Content</h4>
          <pre className="text-xs overflow-auto max-h-96">
            {JSON.stringify(promptContent, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );

  const renderCompletionsTab = () => (
    <div className="space-y-4">
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm">
        <strong>Note:</strong> Completions are used for autocomplete suggestions in resource URIs or prompt arguments.
      </div>

      <div className="space-y-3">
        <label className="block text-sm">
          Ref (JSON):
          <textarea
            value={completionsRef}
            onChange={(e) => setCompletionsRef(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
            rows={2}
            placeholder='{"type":"ref/resource","uri":"file://"}'
          />
        </label>

        <label className="block text-sm">
          Argument (JSON):
          <textarea
            value={completionsArg}
            onChange={(e) => setCompletionsArg(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
            rows={2}
            placeholder='{"name":"path","value":"/home/"}'
          />
        </label>

        <button
          onClick={() => {
            try {
              const ref = JSON.parse(completionsRef);
              const arg = JSON.parse(completionsArg);
              completionsMutation.mutate({ ref, arg });
            } catch (e) {
              setLastError('Invalid JSON in ref or argument');
            }
          }}
          disabled={completionsMutation.isPending}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {completionsMutation.isPending ? 'Testing...' : 'Get Completions'}
        </button>
      </div>

      {completionsResult && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Completions Result</h4>
          <pre className="text-xs overflow-auto">
            {JSON.stringify(completionsResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );

  const renderSessionTab = () => (
    <div className="space-y-4">
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm">
        <strong>Stateful Sessions:</strong> Some MCP servers maintain session state. Use this tab to reset the session and re-initialize.
      </div>

      {connectionData?.sessionId && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Current Session</h4>
          <div className="text-sm">
            <strong>Session ID:</strong> <code className="bg-white px-2 py-1 rounded">{connectionData.sessionId}</code>
          </div>
        </div>
      )}

      <button
        onClick={() => sessionResetMutation.mutate()}
        disabled={sessionResetMutation.isPending}
        className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50"
      >
        {sessionResetMutation.isPending ? 'Resetting...' : 'Reset Session'}
      </button>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-gray-900">MCP Server Tester</h2>
            <p className="text-sm text-gray-600 mt-1">
              Testing: <span className="font-semibold">{serverName}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="px-6 pt-4 border-b border-gray-200 flex gap-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {lastError && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
              <strong>Error:</strong> {lastError}
            </div>
          )}

          {activeTab === 'connection' && renderConnectionTab()}
          {activeTab === 'resources' && renderResourcesTab()}
          {activeTab === 'tools' && renderToolsTab()}
          {activeTab === 'prompts' && renderPromptsTab()}
          {activeTab === 'completions' && renderCompletionsTab()}
          {activeTab === 'session' && renderSessionTab()}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <p className="text-xs text-gray-500">
            MCP Protocol Testing • Project: {projectName}
          </p>
        </div>
      </div>
    </div>
  );
}
