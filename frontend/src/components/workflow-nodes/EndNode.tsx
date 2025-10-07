/**
 * End node for workflow visual editor
 */

import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';

function EndNodeComponent({ selected }: NodeProps) {
  return (
    <div
      className={`px-6 py-3 rounded-full border-2 bg-gradient-to-r from-red-400 to-red-500 text-white shadow-md transition-all ${
        selected ? 'border-red-600 shadow-lg scale-105' : 'border-red-500'
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-red-600"
      />

      <div className="flex items-center gap-2 font-semibold text-sm">
        <span className="text-lg">⏹️</span>
        <span>END</span>
      </div>
    </div>
  );
}

export const EndNode = memo(EndNodeComponent);
