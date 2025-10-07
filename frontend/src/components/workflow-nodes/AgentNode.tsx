/**
 * Custom node type for agents in visual workflow editor
 */

import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import { NodeTooltip } from './NodeTooltip';

export interface AgentNodeData {
  label: string;
  type: string;
  enabled: boolean;
  stepsCount: number;
  tool_name?: string;
  parallel_group?: string;
  timeout?: number;
  template?: string;
  instruction?: string;
}

function AgentNodeComponent({ data, selected }: NodeProps<AgentNodeData>) {
  const hasTimeout = data.timeout && data.timeout > 120;
  const isWarningTimeout = data.timeout && data.timeout > 240;

  return (
    <NodeTooltip
      label={data.label}
      type={data.type}
      instruction={data.instruction}
      timeout={data.timeout}
      tool_name={data.tool_name}
      template={data.template}
      parallel_group={data.parallel_group}
    >
      <div
        className={`px-4 py-3 rounded-lg border-2 bg-white shadow-md min-w-[200px] transition-all ${
          selected
            ? 'border-blue-500 shadow-lg'
            : 'border-gray-300 hover:border-blue-400'
        } ${!data.enabled ? 'opacity-50' : ''}`}
      >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-blue-500"
      />

      <div className="flex items-center gap-2 mb-2">
        <div className="text-2xl">🤖</div>
        <div className="flex-1">
          <div className="font-semibold text-gray-900 text-sm">{data.label}</div>
          <div className="text-xs text-gray-500">{data.type}</div>
        </div>
      </div>

      {/* Badges */}
      <div className="space-y-1 mb-2">
        {data.tool_name && (
          <div className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-purple-100 text-purple-700">
            <span>🔧</span>
            <span className="font-medium">{data.tool_name}</span>
          </div>
        )}
        {data.parallel_group && (
          <div className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-orange-100 text-orange-700">
            <span>⚡</span>
            <span className="font-medium">{data.parallel_group}</span>
          </div>
        )}
        {data.template && (
          <div className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-700">
            <span>📄</span>
            <span className="font-medium">{data.template}</span>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between text-xs flex-wrap gap-1">
        <span className="text-gray-600">{data.stepsCount} steps</span>
        {hasTimeout && (
          <span
            className={`flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] ${
              isWarningTimeout
                ? 'bg-yellow-100 text-yellow-700'
                : 'bg-blue-100 text-blue-700'
            }`}
          >
            <span>⏱️</span>
            <span>{data.timeout}s</span>
          </span>
        )}
        {!data.enabled && (
          <span className="px-1.5 py-0.5 rounded text-[10px] bg-gray-200 text-gray-600">
            disabled
          </span>
        )}
      </div>

        <Handle
          type="source"
          position={Position.Bottom}
          className="w-3 h-3 !bg-blue-500"
        />
      </div>
    </NodeTooltip>
  );
}

export const AgentNode = memo(AgentNodeComponent);
