/**
 * ModelSelector - Dropdown for selecting LLM models
 * Grouped by provider with metadata display
 */

import { useMemo } from 'react';
import type { ModelInfo, ProviderType, APIKeyConfig } from '../types/api';

interface ModelSelectorProps {
  value: string | null;
  onChange: (modelId: string) => void;
  models: ModelInfo[];
  apiKeys?: APIKeyConfig[];
  providers?: ProviderType[];
  placeholder?: string;
  disabled?: boolean;
  showMetadata?: boolean;
}

export function ModelSelector({
  value,
  onChange,
  models,
  apiKeys = [],
  providers,
  placeholder = 'Select a model...',
  disabled = false,
  showMetadata = true,
}: ModelSelectorProps) {
  // Create provider API key lookup
  const providerKeyStatus = useMemo(() => {
    const status: Record<string, boolean> = {};
    apiKeys.forEach((key) => {
      status[key.provider] = key.configured;
    });
    return status;
  }, [apiKeys]);

  // Group models by provider
  const groupedModels = useMemo(() => {
    const groups: Record<string, ModelInfo[]> = {};

    models.forEach((model) => {
      if (!providers || providers.includes(model.provider)) {
        if (!groups[model.provider]) {
          groups[model.provider] = [];
        }
        groups[model.provider].push(model);
      }
    });

    return groups;
  }, [models, providers]);

  // Find selected model for metadata
  const selectedModel = useMemo(() => {
    return models.find((m) => `${m.provider}/${m.model_id}` === value);
  }, [models, value]);

  // Cost tier colors
  const getCostTierColor = (tier: string) => {
    switch (tier) {
      case 'free':
        return 'text-green-600 bg-green-50';
      case 'low':
        return 'text-blue-600 bg-blue-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'high':
        return 'text-orange-600 bg-orange-50';
      case 'premium':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  // Provider display names
  const providerNames: Record<string, string> = {
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    google: 'Google',
    groq: 'Groq',
    openrouter: 'OpenRouter',
  };

  // Format context window for display
  const formatContextWindow = (tokens: number): string => {
    if (tokens >= 1000000) {
      return `${(tokens / 1000000).toFixed(1)}M tokens`;
    } else if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(0)}K tokens`;
    }
    return `${tokens} tokens`;
  };

  // Check if a model can be used (API key configured)
  const isModelAvailable = (model: ModelInfo): boolean => {
    return providerKeyStatus[model.provider] === true;
  };

  return (
    <div className="space-y-2">
      {/* Dropdown */}
      <select
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <option value="">{placeholder}</option>
        {Object.entries(groupedModels).map(([provider, providerModels]) => (
          <optgroup key={provider} label={providerNames[provider] || provider}>
            {providerModels.map((model) => (
              <option key={model.model_id} value={`${model.provider}/${model.model_id}`}>
                {model.display_name}
              </option>
            ))}
          </optgroup>
        ))}
      </select>

      {/* Metadata Display */}
      {showMetadata && selectedModel && (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-3 text-sm space-y-2">
          {/* Provider and Cost */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-700">
                {providerNames[selectedModel.provider] || selectedModel.provider}
              </span>
              {!isModelAvailable(selectedModel) && (
                <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                  🔒 API Key Required
                </span>
              )}
            </div>
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-medium ${getCostTierColor(
                selectedModel.cost_tier
              )}`}
            >
              {selectedModel.cost_tier.toUpperCase()}
            </span>
          </div>

          {/* Technical Details */}
          <div className="grid grid-cols-3 gap-3 text-xs text-gray-600">
            <div className="flex flex-col">
              <span className="font-medium text-gray-700">Context Window</span>
              <span className="mt-1">{formatContextWindow(selectedModel.context_window)}</span>
            </div>
            <div className="flex flex-col">
              <span className="font-medium text-gray-700">Tool Support</span>
              <span className="mt-1">
                {selectedModel.supports_tools ? '✓ Supported' : '✗ Not Available'}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="font-medium text-gray-700">Streaming</span>
              <span className="mt-1">
                {selectedModel.supports_streaming ? '✓ Supported' : '✗ Not Available'}
              </span>
            </div>
          </div>

          {/* Recommended Use Cases */}
          {selectedModel.recommended_for.length > 0 && (
            <div className="pt-2 border-t border-gray-200">
              <div className="text-xs font-medium text-gray-700 mb-1.5">Recommended for:</div>
              <div className="flex flex-wrap gap-1">
                {selectedModel.recommended_for.map((rec) => (
                  <span
                    key={rec}
                    className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium"
                  >
                    {rec.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Warning if API key not configured */}
          {!isModelAvailable(selectedModel) && (
            <div className="pt-2 border-t border-gray-200">
              <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded p-2">
                <span className="text-red-600 text-base">⚠️</span>
                <div className="flex-1 text-xs text-red-700">
                  <div className="font-medium">API Key Required</div>
                  <div className="mt-1">
                    Configure your {providerNames[selectedModel.provider]} API key in the API
                    Providers section to use this model.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
