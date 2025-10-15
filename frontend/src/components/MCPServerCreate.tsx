/**
 * MCP Server creation component
 */

import { useState } from 'react';

interface MCPServerCreateProps {
  onCreate: (serverName: string, config: any) => void;
  onCancel: () => void;
}

export function MCPServerCreate({ onCreate, onCancel }: MCPServerCreateProps) {
  const [serverName, setServerName] = useState('');
  const [config, setConfig] = useState({
    type: 'remote' as 'remote' | 'local',
    transport: 'streamable_http',
    url: '',
    api_key: null as string | null,
    local_path: null as string | null,
    command: null as string | null,
    enabled: true,
    timeout: 60,
  });

  const [nameError, setNameError] = useState<string | null>(null);

  const handleCreate = () => {
    // Validate server name
    if (!serverName.trim()) {
      setNameError('Server name is required');
      return;
    }

    // Validate name format (alphanumeric, underscores, hyphens)
    if (!/^[a-zA-Z0-9_-]+$/.test(serverName)) {
      setNameError('Server name can only contain letters, numbers, underscores, and hyphens');
      return;
    }

    // Validate URL for remote servers
    if (config.type === 'remote' && !config.url.trim()) {
      alert('URL is required for remote servers');
      return;
    }

    // Validate local path for local servers
    if (config.type === 'local' && !config.local_path?.trim()) {
      alert('Local path is required for local servers');
      return;
    }

    onCreate(serverName.trim(), config);
  };

  return (
    <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold">Create New MCP Server</h3>
            <p className="text-sm text-blue-100 mt-1">
              Configure a new Model Context Protocol server
            </p>
          </div>
          <button
            onClick={onCancel}
            className="px-3 py-1.5 text-sm font-medium bg-white/20 hover:bg-white/30 rounded-md"
          >
            ✕ Cancel
          </button>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="p-4 space-y-4">
        {/* Server Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Server Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={serverName}
            onChange={(e) => {
              setServerName(e.target.value);
              setNameError(null);
            }}
            placeholder="my-mcp-server"
            className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 ${
              nameError ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {nameError && <div className="text-sm text-red-600 mt-1">{nameError}</div>}
          <div className="text-xs text-gray-500 mt-1">
            Use only letters, numbers, underscores, and hyphens
          </div>
        </div>

        {/* Enabled Toggle */}
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">Enabled</label>
          <button
            onClick={() => setConfig({ ...config, enabled: !config.enabled })}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              config.enabled ? 'bg-blue-600' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                config.enabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {/* Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
          <select
            value={config.type}
            onChange={(e) =>
              setConfig({ ...config, type: e.target.value as 'remote' | 'local' })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
          >
            <option value="remote">Remote</option>
            <option value="local">Local</option>
          </select>
        </div>

        {/* Remote Config */}
        {config.type === 'remote' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                URL <span className="text-red-500">*</span>
              </label>
              <input
                type="url"
                value={config.url || ''}
                onChange={(e) => setConfig({ ...config, url: e.target.value })}
                placeholder="http://localhost:8005/mcp"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Bearer Token (optional)
              </label>
              <input
                type="password"
                value={config.api_key || ''}
                onChange={(e) =>
                  setConfig({ ...config, api_key: e.target.value || null })
                }
                placeholder="sk-..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
              <div className="text-xs text-gray-500 mt-1">
                Sent as Authorization: Bearer &lt;token&gt; header
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Transport
              </label>
              <select
                value={config.transport || 'streamable_http'}
                onChange={(e) => setConfig({ ...config, transport: e.target.value })}
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
        {config.type === 'local' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Local Path <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={config.local_path || ''}
                onChange={(e) =>
                  setConfig({ ...config, local_path: e.target.value || null })
                }
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
                value={config.command || ''}
                onChange={(e) =>
                  setConfig({ ...config, command: e.target.value || null })
                }
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
            value={config.timeout || 60}
            onChange={(e) => setConfig({ ...config, timeout: parseInt(e.target.value) })}
            min="1"
            max="300"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Create Button */}
        <button
          onClick={handleCreate}
          className="w-full px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-purple-600 rounded-md hover:from-blue-700 hover:to-purple-700 shadow-md"
        >
          ✨ Create Server
        </button>
      </div>
    </div>
  );
}
