/**
 * Rich tooltip component for workflow nodes
 */

import { useState } from 'react';

interface NodeTooltipProps {
  label: string;
  type: string;
  instruction?: string;
  timeout?: number;
  tool_name?: string;
  template?: string;
  parallel_group?: string;
  children: React.ReactNode;
}

export function NodeTooltip({
  label,
  type,
  instruction,
  timeout,
  tool_name,
  template,
  parallel_group,
  children,
}: NodeTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div
      className="relative"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}

      {isVisible && (
        <div
          className="absolute z-50 w-80 p-4 bg-white rounded-lg shadow-xl border-2 border-gray-200"
          style={{
            bottom: '100%',
            left: '50%',
            transform: 'translateX(-50%)',
            marginBottom: '10px',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Arrow */}
          <div
            className="absolute w-3 h-3 bg-white border-r-2 border-b-2 border-gray-200"
            style={{
              bottom: '-7px',
              left: '50%',
              transform: 'translateX(-50%) rotate(45deg)',
            }}
          />

          {/* Header */}
          <div className="mb-3 pb-3 border-b border-gray-200">
            <div className="font-bold text-gray-900 text-sm mb-1">{label}</div>
            <div className="text-xs text-gray-500">Agent: {type}</div>
          </div>

          {/* Properties */}
          <div className="space-y-2 text-xs">
            {tool_name && (
              <div className="flex items-start gap-2">
                <span className="font-semibold text-purple-700 min-w-[60px]">MCP Tool:</span>
                <span className="text-gray-700 font-mono text-[11px]">{tool_name}</span>
              </div>
            )}

            {parallel_group && (
              <div className="flex items-start gap-2">
                <span className="font-semibold text-orange-700 min-w-[60px]">Parallel:</span>
                <span className="text-gray-700">{parallel_group}</span>
              </div>
            )}

            {template && (
              <div className="flex items-start gap-2">
                <span className="font-semibold text-gray-700 min-w-[60px]">Template:</span>
                <span className="text-gray-700">{template}</span>
              </div>
            )}

            {timeout && (
              <div className="flex items-start gap-2">
                <span className="font-semibold text-blue-700 min-w-[60px]">Timeout:</span>
                <span className={timeout > 240 ? 'text-yellow-700 font-semibold' : 'text-gray-700'}>
                  {timeout} seconds
                  {timeout > 240 && ' ⚠️'}
                </span>
              </div>
            )}

            {instruction && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="font-semibold text-gray-700 mb-1">Instruction:</div>
                <div className="text-gray-600 text-[11px] leading-relaxed max-h-40 overflow-y-auto bg-gray-50 p-2 rounded">
                  {instruction.length > 300
                    ? instruction.substring(0, 300) + '...'
                    : instruction}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
