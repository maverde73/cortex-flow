/**
 * Start node for workflow visual editor
 */

import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';

function StartNodeComponent({ selected }: NodeProps) {
  return (
    <div
      className={`px-6 py-3 rounded-full border-2 bg-gradient-to-r from-green-400 to-green-500 text-white shadow-md transition-all ${
        selected ? 'border-green-600 shadow-lg scale-105' : 'border-green-500'
      }`}
    >
      <div className="flex items-center gap-2 font-semibold text-sm">
        <span className="text-lg">▶️</span>
        <span>START</span>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-green-600"
      />
    </div>
  );
}

export const StartNode = memo(StartNodeComponent);
