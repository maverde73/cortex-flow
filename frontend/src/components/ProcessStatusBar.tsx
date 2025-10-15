/**
 * Process Status Bar Component
 *
 * Displays status of running processes (agents) with simple toggle controls.
 * Click to start/stop agents. Auto-refreshes every 5 seconds.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import type { ProcessInfo } from '../types/api';

interface ProcessBadgeProps {
  process: ProcessInfo;
  onToggle: () => void;
}

function ProcessBadge({ process, onToggle }: ProcessBadgeProps) {
  const statusColor = {
    running: 'bg-green-500 hover:bg-green-600',
    stopped: 'bg-gray-400 hover:bg-gray-500',
    starting: 'bg-yellow-500 hover:bg-yellow-600',
    error: 'bg-red-500 hover:bg-red-600',
  }[process.status];

  const statusIcon = {
    running: '🟢',
    stopped: '⚪',
    starting: '🟡',
    error: '🔴',
  }[process.status];

  const formatUptime = (seconds: number) => {
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h`;
  };

  return (
    <button
      onClick={onToggle}
      className={`px-3 py-1 rounded-full text-xs font-medium text-white transition-all cursor-pointer ${statusColor}`}
      title={`Click to ${process.status === 'running' ? 'stop' : 'start'} ${process.name}`}
    >
      {statusIcon} {process.name}
      {process.status === 'running' && ` (${formatUptime(process.uptime_seconds)})`}
    </button>
  );
}

export function ProcessStatusBar() {
  const queryClient = useQueryClient();

  // Fetch process status every 5 seconds
  const { data: processes = [] } = useQuery({
    queryKey: ['processes-status'],
    queryFn: () => api.getProcessesStatus(),
    refetchInterval: 5000,
  });

  // Mutations
  const startProcessMutation = useMutation({
    mutationFn: (name: string) => api.startProcess(name),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['processes-status'] }),
  });

  const stopProcessMutation = useMutation({
    mutationFn: (name: string) => api.stopProcess(name),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['processes-status'] }),
  });

  const startAllMutation = useMutation({
    mutationFn: () => api.startAllProcesses(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['processes-status'] }),
  });

  const stopAllMutation = useMutation({
    mutationFn: () => api.stopAllProcesses(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['processes-status'] }),
  });

  const handleProcessToggle = (process: ProcessInfo) => {
    console.log(`Toggling ${process.name}: ${process.status} -> ${process.status === 'running' ? 'stopped' : 'running'}`);

    if (process.status === 'running') {
      stopProcessMutation.mutate(process.name);
    } else {
      startProcessMutation.mutate(process.name);
    }
  };

  const runningCount = processes.filter(p => p.status === 'running').length;
  const totalCount = processes.length;

  return (
    <>
      <div className="bg-white border-t border-gray-200 px-4 py-2">
        <div className="flex items-center justify-between gap-4">
          {/* Process badges */}
          <div className="flex items-center gap-2 flex-wrap">
            {processes.map((process) => (
              <ProcessBadge
                key={process.name}
                process={process}
                onToggle={() => handleProcessToggle(process)}
              />
            ))}
          </div>

          {/* Global controls */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">
              Running: {runningCount}/{totalCount}
            </span>
            <button
              onClick={() => startAllMutation.mutate()}
              disabled={startAllMutation.isPending}
              className="px-3 py-1 text-xs font-medium text-green-700 bg-green-100 rounded hover:bg-green-200 disabled:opacity-50"
            >
              ▶️ Start All
            </button>
            <button
              onClick={() => stopAllMutation.mutate()}
              disabled={stopAllMutation.isPending}
              className="px-3 py-1 text-xs font-medium text-red-700 bg-red-100 rounded hover:bg-red-200 disabled:opacity-50"
            >
              ⏹️ Stop All
            </button>
            <button
              onClick={() => queryClient.invalidateQueries({ queryKey: ['processes-status'] })}
              className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded hover:bg-blue-200"
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      </div>
    </>
  );
}