/**
 * Condition/routing node for workflow visual editor
 */

import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';

export interface ConditionNodeData {
  label: string;
  condition?: string;
}

function ConditionNodeComponent({ data, selected }: NodeProps<ConditionNodeData>) {
  return (
    <div
      className={`relative ${selected ? 'scale-105' : ''} transition-all`}
      style={{ width: 120, height: 120 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-yellow-500"
      />

      <div
        className={`w-full h-full transform rotate-45 border-2 bg-yellow-50 shadow-md ${
          selected ? 'border-yellow-500 shadow-lg' : 'border-yellow-400'
        }`}
      >
        <div className="absolute inset-0 flex items-center justify-center transform -rotate-45">
          <div className="text-center px-2">
            <div className="text-xl mb-1">🔀</div>
            <div className="text-xs font-medium text-gray-900">{data.label}</div>
            {data.condition && (
              <div className="text-[10px] text-gray-500 mt-1 line-clamp-1">
                {data.condition}
              </div>
            )}
          </div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        id="true"
        className="w-3 h-3 !bg-green-500"
        style={{ top: '50%', right: -6 }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="false"
        className="w-3 h-3 !bg-red-500"
        style={{ left: '50%', bottom: -6 }}
      />
    </div>
  );
}

export const ConditionNode = memo(ConditionNodeComponent);
