/**
 * MCP Registry browser component
 */

import { useState } from 'react';
import type { MCPServerDetails } from '../types/api';

interface MCPBrowserProps {
  servers: Array<{ id: string; name: string; description: string; repository?: string }>;
  onAddServer: (serverId: string) => void;
  installedServers: string[];
}

export function MCPBrowser({ servers, onAddServer, installedServers }: MCPBrowserProps) {
  const [selectedServer, setSelectedServer] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredServers = servers.filter(
    (server) =>
      server.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      server.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const selectedServerData = servers.find((s) => s.id === selectedServer);

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Server List */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">MCP Registry</h3>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search servers..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div className="space-y-2 max-h-96 overflow-y-auto">
          {filteredServers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No servers found</div>
          ) : (
            filteredServers.map((server) => {
              const isInstalled = installedServers.includes(server.id);
              return (
                <div
                  key={server.id}
                  onClick={() => setSelectedServer(server.id)}
                  className={`p-4 border rounded-lg cursor-pointer transition-all ${
                    selectedServer === server.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start justify-between mb-1">
                    <div className="font-medium text-gray-900">{server.name}</div>
                    {isInstalled && (
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                        Installed
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-600 line-clamp-2">{server.description}</div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Server Details */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-6">
        {selectedServerData ? (
          <div className="space-y-4">
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                {selectedServerData.name}
              </h3>
              <p className="text-gray-600">{selectedServerData.description}</p>
            </div>

            {selectedServerData.repository && (
              <div>
                <div className="text-sm font-medium text-gray-700 mb-1">Repository</div>
                <a
                  href={selectedServerData.repository}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:text-blue-700 hover:underline"
                >
                  {selectedServerData.repository}
                </a>
              </div>
            )}

            <div className="pt-4 border-t">
              {installedServers.includes(selectedServerData.id) ? (
                <div className="flex items-center gap-2 text-green-600">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="font-medium">Already installed</span>
                </div>
              ) : (
                <button
                  onClick={() => onAddServer(selectedServerData.id)}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  + Add to Project
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <svg
                className="w-16 h-16 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p>Select a server to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
