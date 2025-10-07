/**
 * APIKeyManager - Manage API keys for all LLM providers
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import type { APIKeyConfig, ProviderType } from '../types/api';

interface APIKeyManagerProps {
  apiKeys: APIKeyConfig[];
  isLoading?: boolean;
}

const providerInfo: Record<
  ProviderType,
  { name: string; color: string; signupUrl: string; description: string }
> = {
  openai: {
    name: 'OpenAI',
    color: 'bg-green-500',
    signupUrl: 'https://platform.openai.com/api-keys',
    description: 'GPT-4o, O1, and other OpenAI models',
  },
  anthropic: {
    name: 'Anthropic',
    color: 'bg-orange-500',
    signupUrl: 'https://console.anthropic.com/',
    description: 'Claude 4 Opus, Sonnet, and Haiku models',
  },
  google: {
    name: 'Google AI',
    color: 'bg-blue-500',
    signupUrl: 'https://makersuite.google.com/app/apikey',
    description: 'Gemini 2.0 and 1.5 models with long context',
  },
  groq: {
    name: 'Groq',
    color: 'bg-purple-500',
    signupUrl: 'https://console.groq.com/',
    description: 'Ultra-fast LLama and Mixtral inference',
  },
  openrouter: {
    name: 'OpenRouter',
    color: 'bg-red-500',
    signupUrl: 'https://openrouter.ai/keys',
    description: 'Unified access to all models via single API',
  },
};

export function APIKeyManager({ apiKeys, isLoading }: APIKeyManagerProps) {
  const [editingProvider, setEditingProvider] = useState<string | null>(null);
  const [newKey, setNewKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [validatingProvider, setValidatingProvider] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Update API key mutation
  const updateKeyMutation = useMutation({
    mutationFn: ({ provider, key }: { provider: string; key: string }) =>
      api.updateAPIKey(provider, key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
      setEditingProvider(null);
      setNewKey('');
      setShowKey(false);
    },
  });

  // Validate API key mutation
  const validateKeyMutation = useMutation({
    mutationFn: (provider: string) => api.validateAPIKey(provider),
    onSuccess: (data, provider) => {
      const icon = data.valid ? '✅' : '❌';
      const status = data.valid ? 'Valid' : 'Invalid';
      const message = data.error || data.model_info || '';
      alert(`${icon} ${providerInfo[provider as ProviderType].name} API Key\n\n${status}\n${message}`);
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
    },
    onError: (error: any, provider) => {
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      alert(`❌ Validation Failed\n\n${providerInfo[provider as ProviderType].name}\n${errorMsg}`);
    },
    onSettled: () => {
      setValidatingProvider(null);
    },
  });

  const handleSave = (provider: string) => {
    if (!newKey.trim()) {
      alert('Please enter an API key');
      return;
    }

    updateKeyMutation.mutate({ provider, key: newKey.trim() });
  };

  const handleCancel = () => {
    setEditingProvider(null);
    setNewKey('');
    setShowKey(false);
  };

  const handleValidate = (provider: string) => {
    setValidatingProvider(provider);
    validateKeyMutation.mutate(provider);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-600">Loading API keys...</div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {apiKeys.map((keyConfig) => {
        const info = providerInfo[keyConfig.provider];
        const isEditing = editingProvider === keyConfig.provider;
        const isValidating = validatingProvider === keyConfig.provider;

        return (
          <div
            key={keyConfig.provider}
            className="border border-gray-200 rounded-lg bg-white overflow-hidden"
          >
            {/* Header */}
            <div
              className={`p-4 text-white ${info.color} bg-gradient-to-r from-${info.color} to-${info.color}/80`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-white/30" />
                  <div>
                    <h3 className="font-bold text-lg">{info.name}</h3>
                    <p className="text-sm text-white/90 mt-0.5">{info.description}</p>
                  </div>
                </div>

                {/* Status Badge */}
                <div>
                  {keyConfig.configured ? (
                    <span className="px-3 py-1 bg-white/20 rounded-full text-sm font-medium">
                      ✓ Configured
                    </span>
                  ) : (
                    <span className="px-3 py-1 bg-white/10 rounded-full text-sm font-medium">
                      ⚠ Not Set
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Body */}
            <div className="p-4 space-y-3">
              {isEditing ? (
                // Edit Mode
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      API Key
                    </label>
                    <div className="relative">
                      <input
                        type={showKey ? 'text' : 'password'}
                        value={newKey}
                        onChange={(e) => setNewKey(e.target.value)}
                        placeholder={`Enter ${info.name} API key...`}
                        className="w-full px-3 py-2 pr-20 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                        autoFocus
                      />
                      <button
                        onClick={() => setShowKey(!showKey)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 px-2 py-1 text-xs text-gray-600 hover:text-gray-900"
                      >
                        {showKey ? '🙈 Hide' : '👁️ Show'}
                      </button>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={handleCancel}
                      disabled={updateKeyMutation.isPending}
                      className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleSave(keyConfig.provider)}
                      disabled={updateKeyMutation.isPending}
                      className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {updateKeyMutation.isPending ? 'Saving...' : 'Save Key'}
                    </button>
                  </div>
                </>
              ) : (
                // View Mode
                <>
                  {keyConfig.configured && keyConfig.masked_key ? (
                    <div className="bg-gray-50 rounded-md p-3">
                      <div className="text-xs text-gray-500 mb-1">Current API Key</div>
                      <div className="font-mono text-sm text-gray-900">{keyConfig.masked_key}</div>
                    </div>
                  ) : (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                      <div className="flex items-start gap-2">
                        <span className="text-yellow-600 text-lg">⚠️</span>
                        <div className="flex-1">
                          <div className="text-sm font-medium text-yellow-800">
                            No API Key Configured
                          </div>
                          <div className="text-xs text-yellow-600 mt-1">
                            Models from this provider will not be available until you add an API key.
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setEditingProvider(keyConfig.provider);
                        setNewKey('');
                      }}
                      disabled={updateKeyMutation.isPending}
                      className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {keyConfig.configured ? '✏️ Update Key' : '➕ Add Key'}
                    </button>

                    {keyConfig.configured && (
                      <button
                        onClick={() => handleValidate(keyConfig.provider)}
                        disabled={isValidating}
                        className="flex-1 px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-300 rounded-md hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isValidating ? '⏳ Testing...' : '🧪 Test Connection'}
                      </button>
                    )}

                    <a
                      href={info.signupUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-50 border border-gray-300 rounded-md hover:bg-gray-100"
                      title={`Get ${info.name} API key`}
                    >
                      🔗
                    </a>
                  </div>
                </>
              )}

              {/* Help Text */}
              {!isEditing && (
                <div className="text-xs text-gray-500 pt-2 border-t border-gray-100">
                  💡 Get your API key at{' '}
                  <a
                    href={info.signupUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {info.signupUrl.replace('https://', '')}
                  </a>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
