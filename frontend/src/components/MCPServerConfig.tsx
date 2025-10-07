/**
 * MCP Server configuration component
 */

import { useState } from 'react';

interface MCPServerConfigProps {
  serverId: string;
  serverName: string;
  config: {
    type: 'remote' | 'local';
    transport?: string;
    url?: string;
    api_key?: string | null;
    local_path?: string | null;
    enabled: boolean;
    timeout?: number;
  };
  onUpdate: (serverId: string, config: any) => void;
  onRemove: (serverId: string) => void;
  onTest: (serverId: string) => void;
  isTesting?: boolean;
}

export function MCPServerConfig({
  serverId,
  serverName,
  config,
  onUpdate,
  onRemove,
  onTest,
  isTesting = false,
}: MCPServerConfigProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localConfig, setLocalConfig] = useState(config);

  const handleUpdate = () => {
    onUpdate(serverId, localConfig);
  };

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div
        className="bg-white p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <div
            className={`w-3 h-3 rounded-full ${
              localConfig.enabled ? 'bg-green-500' : 'bg-gray-300'
            }`}
          />
          <div>
            <div className="font-medium text-gray-900">{serverName}</div>
            <div className="text-sm text-gray-500">
              {localConfig.type === 'remote' ? `Remote: ${localConfig.url}` : 'Local'}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onTest(serverId);
            }}
            disabled={isTesting}
            className="px-3 py-1 text-sm text-blue-600 border border-blue-300 rounded hover:bg-blue-50 disabled:opacity-50"
          >
            {isTesting ? 'Testing...' : '🔌 Test'}
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onRemove(serverId);
            }}
            className="px-3 py-1 text-sm text-red-600 border border-red-300 rounded hover:bg-red-50"
          >
            Remove
          </button>
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform ${
              isExpanded ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Expanded Configuration */}
      {isExpanded && (
        <div className="bg-gray-50 p-4 border-t space-y-4">
          {/* Enabled Toggle */}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-700">Enabled</label>
            <button
              onClick={() => setLocalConfig({ ...localConfig, enabled: !localConfig.enabled })}
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
          </div>

          {/* Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select
              value={localConfig.type}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, type: e.target.value as 'remote' | 'local' })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="remote">Remote</option>
              <option value="local">Local</option>
            </select>
          </div>

          {/* Remote Config */}
          {localConfig.type === 'remote' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
                <input
                  type="url"
                  value={localConfig.url || ''}
                  onChange={(e) => setLocalConfig({ ...localConfig, url: e.target.value })}
                  placeholder="http://localhost:8000/mcp"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key (optional)
                </label>
                <input
                  type="password"
                  value={localConfig.api_key || ''}
                  onChange={(e) => setLocalConfig({ ...localConfig, api_key: e.target.value })}
                  placeholder="sk-..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Transport
                </label>
                <select
                  value={localConfig.transport || 'streamable_http'}
                  onChange={(e) => setLocalConfig({ ...localConfig, transport: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="streamable_http">Streamable HTTP</option>
                  <option value="http">HTTP</option>
                  <option value="sse">Server-Sent Events</option>
                </select>
              </div>
            </>
          )}

          {/* Local Config */}
          {localConfig.type === 'local' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Local Path</label>
                <input
                  type="text"
                  value={localConfig.local_path || ''}
                  onChange={(e) => setLocalConfig({ ...localConfig, local_path: e.target.value })}
                  placeholder="/path/to/mcp-server"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Command
                </label>
                <input
                  type="text"
                  value={(localConfig as any).command || ''}
                  onChange={(e) => setLocalConfig({ ...localConfig, command: e.target.value } as any)}
                  placeholder="node server.js"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </>
          )}

          {/* Timeout */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Timeout (seconds)
            </label>
            <input
              type="number"
              value={localConfig.timeout || 30}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, timeout: parseInt(e.target.value) })
              }
              min="1"
              max="300"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Save Button */}
          <button
            onClick={handleUpdate}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Save Configuration
          </button>
        </div>
      )}
    </div>
  );
}
