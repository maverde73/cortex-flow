/**
 * Testing & Debugging Page
 *
 * Test agents standalone and debug workflows with detailed step-by-step execution
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import { useStore } from '../store/useStore';
import type {
  AgentInvokeRequest,
  WorkflowExecuteRequest,
  ExecutionResult,
  ExecutionStep,
} from '../types/api';

type TabMode = 'agents' | 'workflows';

export function TestingPage() {
  const [mode, setMode] = useState<TabMode>('agents');
  const { currentProject } = useStore();
  const projectName = currentProject?.name || 'default';

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Testing & Debugging</h1>
        <p className="text-gray-600 mt-2">
          Test agents and workflows with detailed execution traces
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        <button
          onClick={() => setMode('agents')}
          className={`px-6 py-3 font-medium transition-colors border-b-2 ${
            mode === 'agents'
              ? 'text-blue-600 border-blue-600'
              : 'text-gray-600 border-transparent hover:text-gray-900'
          }`}
        >
          🤖 Agent Playground
        </button>
        <button
          onClick={() => setMode('workflows')}
          className={`px-6 py-3 font-medium transition-colors border-b-2 ${
            mode === 'workflows'
              ? 'text-blue-600 border-blue-600'
              : 'text-gray-600 border-transparent hover:text-gray-900'
          }`}
        >
          🔄 Workflow Debugger
        </button>
      </div>

      {/* Content */}
      {mode === 'agents' ? (
        <AgentPlayground projectName={projectName} />
      ) : (
        <WorkflowDebugger projectName={projectName} />
      )}
    </div>
  );
}

// ============================================================================
// Agent Playground Component
// ============================================================================

interface AgentPlaygroundProps {
  projectName: string;
}

function AgentPlayground({ projectName }: AgentPlaygroundProps) {
  const [selectedAgent, setSelectedAgent] = useState('');
  const [task, setTask] = useState('');
  const [result, setResult] = useState<ExecutionResult | null>(null);

  // Fetch agents config
  const { data: agentsConfig, isLoading: isLoadingAgents } = useQuery({
    queryKey: ['agents-config', projectName],
    queryFn: () => api.getAgentsConfig(projectName),
  });

  // Invoke agent mutation
  const invokeMutation = useMutation({
    mutationFn: (request: AgentInvokeRequest) => api.invokeAgent(request),
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const agents = agentsConfig?.agents || {};
  const agentList = Object.entries(agents).filter(([_, config]) => config.enabled);

  const handleInvoke = () => {
    if (!selectedAgent || !task.trim()) return;

    invokeMutation.mutate({
      agent_name: selectedAgent,
      task: task,
      project_name: projectName,
    });
  };

  // Check agent health
  const { data: healthData, refetch: checkHealth } = useQuery({
    queryKey: ['agent-health', selectedAgent, projectName],
    queryFn: () => api.checkAgentHealth(selectedAgent, projectName),
    enabled: !!selectedAgent,
  });

  if (isLoadingAgents) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Agent Selection */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Agent</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agentList.map(([agentName, config]) => (
            <button
              key={agentName}
              onClick={() => setSelectedAgent(agentName)}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                selectedAgent === agentName
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-semibold text-gray-900">{agentName}</div>
                  <div className="text-sm text-gray-600 mt-1">
                    {config.model || 'default model'}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {config.react_strategy} • {config.temperature}°
                  </div>
                </div>
                {selectedAgent === agentName && healthData && (
                  <span className={`inline-block w-3 h-3 rounded-full ${
                    healthData.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                )}
              </div>
            </button>
          ))}
        </div>

        {agentList.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No enabled agents found. Enable agents in the Agents page.
          </div>
        )}
      </div>

      {/* Agent Health Status */}
      {selectedAgent && healthData && (
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className={`inline-block w-3 h-3 rounded-full ${
                healthData.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <span className="font-medium text-gray-900">
                Agent Status: {healthData.status}
              </span>
              {healthData.url && (
                <span className="text-sm text-gray-600">({healthData.url})</span>
              )}
            </div>
            <button
              onClick={() => checkHealth()}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              Refresh
            </button>
          </div>
          {healthData.error && (
            <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
              {healthData.error}
            </div>
          )}
        </div>
      )}

      {/* Task Input */}
      {selectedAgent && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Task Input</h2>

          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="Enter task for the agent... (e.g., 'Find the latest news about AI')"
            className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          />

          <div className="mt-4 flex gap-3">
            <button
              onClick={handleInvoke}
              disabled={!task.trim() || invokeMutation.isPending || healthData?.status !== 'healthy'}
              className="flex-1 px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {invokeMutation.isPending ? (
                <>
                  <span className="inline-block animate-spin mr-2">⚙️</span>
                  Executing...
                </>
              ) : (
                '▶️ Invoke Agent'
              )}
            </button>
            <button
              onClick={() => { setTask(''); setResult(null); }}
              className="px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <ExecutionResultView result={result} />
      )}
    </div>
  );
}

// ============================================================================
// Workflow Debugger Component
// ============================================================================

interface WorkflowDebuggerProps {
  projectName: string;
}

function WorkflowDebugger({ projectName }: WorkflowDebuggerProps) {
  const [selectedWorkflow, setSelectedWorkflow] = useState('');
  const [userInput, setUserInput] = useState('');
  const [parameters, setParameters] = useState('{}');
  const [result, setResult] = useState<ExecutionResult | null>(null);

  // Fetch workflows
  const { data: workflows, isLoading } = useQuery({
    queryKey: ['workflows', projectName],
    queryFn: () => api.listWorkflows(projectName),
  });

  // Execute workflow mutation
  const executeMutation = useMutation({
    mutationFn: (request: WorkflowExecuteRequest) => api.executeWorkflow(request),
    onSuccess: async (data) => {
      // Set initial result immediately
      setResult(data);

      // If execution_id is present, fetch detailed logs
      if (data.execution_id) {
        try {
          const logsResponse = await api.getWorkflowLogs(data.execution_id);

          // Update result with logs if fetch was successful
          if (logsResponse.success && logsResponse.steps.length > 0) {
            setResult({
              ...data,
              steps: logsResponse.steps,  // Replace steps with logs
              metadata: {
                ...data.metadata,
                ...logsResponse.metadata,
                logs_source: 'file',  // Mark that steps came from log file
              }
            });
          }
        } catch (error) {
          console.error('Failed to fetch workflow logs:', error);
          // Keep the initial result if logs fetch fails
        }
      }
    },
  });

  const handleExecute = () => {
    if (!selectedWorkflow || !userInput.trim()) return;

    let params = {};
    try {
      params = JSON.parse(parameters);
    } catch (e) {
      alert('Invalid JSON in parameters');
      return;
    }

    executeMutation.mutate({
      workflow_name: selectedWorkflow,
      user_input: userInput,
      project_name: projectName,
      parameters: params,
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Workflow Selection */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Workflow</h2>

        <select
          value={selectedWorkflow}
          onChange={(e) => setSelectedWorkflow(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="">-- Select a workflow --</option>
          {workflows?.map((workflow) => (
            <option key={workflow.name} value={workflow.name}>
              {workflow.name}
            </option>
          ))}
        </select>
      </div>

      {/* Input */}
      {selectedWorkflow && (
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              User Input
            </label>
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Enter input for the workflow..."
              className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Parameters (JSON)
            </label>
            <textarea
              value={parameters}
              onChange={(e) => setParameters(e.target.value)}
              placeholder='{"key": "value"}'
              className="w-full h-24 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm resize-none"
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleExecute}
              disabled={!userInput.trim() || executeMutation.isPending}
              className="flex-1 px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {executeMutation.isPending ? (
                <>
                  <span className="inline-block animate-spin mr-2">⚙️</span>
                  Executing...
                </>
              ) : (
                '▶️ Execute Workflow'
              )}
            </button>
            <button
              onClick={() => { setUserInput(''); setParameters('{}'); setResult(null); }}
              className="px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <ExecutionResultView result={result} />
      )}
    </div>
  );
}

// ============================================================================
// Step Detail View Component
// ============================================================================

interface StepDetailViewProps {
  step: ExecutionStep;
}

function StepDetailView({ step }: StepDetailViewProps) {
  const [copiedSection, setCopiedSection] = useState<string | null>(null);

  const copyToClipboard = (text: string, section: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(section);
    setTimeout(() => setCopiedSection(null), 2000);
  };

  const truncate = (text: string, maxLength: number = 1000) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + `... (${text.length - maxLength} more chars)`;
  };

  const formatJson = (obj: any) => {
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return String(obj);
    }
  };

  const renderCopyButton = (content: string, section: string) => (
    <button
      onClick={() => copyToClipboard(content, section)}
      className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
    >
      {copiedSection === section ? '✓ Copied' : 'Copy'}
    </button>
  );

  // Render different views based on agent type
  const renderLLMDetails = () => (
    <div className="space-y-4">
      {step.metadata.instruction && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">📄 Instruction (Prompt)</span>
            {renderCopyButton(step.metadata.instruction, 'instruction')}
          </div>
          <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto whitespace-pre-wrap">
            {truncate(step.metadata.instruction, 2000)}
          </pre>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-sm font-semibold text-gray-700 mb-1">⚙️ Configuration</div>
          <div className="text-xs bg-white p-2 rounded border border-gray-200">
            {step.metadata.model && <div><strong>Model:</strong> {step.metadata.model}</div>}
            {step.metadata.provider && <div><strong>Provider:</strong> {step.metadata.provider}</div>}
            {step.metadata.temperature !== undefined && <div><strong>Temperature:</strong> {step.metadata.temperature}</div>}
            {step.metadata.max_tokens && <div><strong>Max Tokens:</strong> {step.metadata.max_tokens}</div>}
          </div>
        </div>

        <div>
          <div className="text-sm font-semibold text-gray-700 mb-1">⏱️ Execution</div>
          <div className="text-xs bg-white p-2 rounded border border-gray-200">
            {step.metadata.execution_time && <div><strong>Time:</strong> {step.metadata.execution_time.toFixed(2)}s</div>}
            {step.metadata.output_length && <div><strong>Output Length:</strong> {step.metadata.output_length} chars</div>}
            {step.iteration > 1 && <div><strong>Retry:</strong> Attempt {step.iteration}</div>}
          </div>
        </div>
      </div>

      {step.content && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">📤 Output</span>
            {renderCopyButton(step.content, 'output')}
          </div>
          <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto whitespace-pre-wrap">
            {truncate(step.content, 2000)}
          </pre>
        </div>
      )}
    </div>
  );

  const renderMCPToolDetails = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-sm font-semibold text-gray-700 mb-1">🔧 Tool Information</div>
          <div className="text-xs bg-white p-2 rounded border border-gray-200">
            {step.metadata.tool_name && <div><strong>Tool:</strong> {step.metadata.tool_name}</div>}
            {step.metadata.server_name && <div><strong>Server:</strong> {step.metadata.server_name}</div>}
          </div>
        </div>

        <div>
          <div className="text-sm font-semibold text-gray-700 mb-1">⏱️ Execution</div>
          <div className="text-xs bg-white p-2 rounded border border-gray-200">
            {step.metadata.execution_time && <div><strong>Time:</strong> {step.metadata.execution_time.toFixed(2)}s</div>}
            {step.metadata.output_length && <div><strong>Output Length:</strong> {step.metadata.output_length} chars</div>}
          </div>
        </div>
      </div>

      {step.metadata.instruction && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">📥 Input Arguments</span>
            {renderCopyButton(step.metadata.instruction, 'input')}
          </div>
          <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto whitespace-pre-wrap">
            {truncate(step.metadata.instruction, 1500)}
          </pre>
        </div>
      )}

      {step.content && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">📤 Response</span>
            {renderCopyButton(step.content, 'response')}
          </div>
          <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto whitespace-pre-wrap">
            {truncate(step.content, 2000)}
          </pre>
        </div>
      )}
    </div>
  );

  const renderMCPResourceDetails = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-sm font-semibold text-gray-700 mb-1">📚 Resource Information</div>
          <div className="text-xs bg-white p-2 rounded border border-gray-200">
            {step.metadata.resource_uri && <div><strong>URI:</strong> {step.metadata.resource_uri}</div>}
            {step.metadata.server_name && <div><strong>Server:</strong> {step.metadata.server_name}</div>}
          </div>
        </div>

        <div>
          <div className="text-sm font-semibold text-gray-700 mb-1">⏱️ Execution</div>
          <div className="text-xs bg-white p-2 rounded border border-gray-200">
            {step.metadata.execution_time && <div><strong>Time:</strong> {step.metadata.execution_time.toFixed(2)}s</div>}
            {step.metadata.output_length && <div><strong>Output Length:</strong> {step.metadata.output_length} chars</div>}
          </div>
        </div>
      </div>

      {step.content && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">📤 Resource Content</span>
            {renderCopyButton(step.content, 'content')}
          </div>
          <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto whitespace-pre-wrap">
            {truncate(step.content, 2000)}
          </pre>
        </div>
      )}
    </div>
  );

  const renderGenericDetails = () => (
    <div className="space-y-4">
      {step.content && (
        <div>
          <div className="text-sm font-semibold text-gray-700 mb-2">📄 Content</div>
          <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto whitespace-pre-wrap">
            {truncate(step.content, 2000)}
          </pre>
        </div>
      )}

      {Object.keys(step.metadata).length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">🔍 Metadata</span>
            {renderCopyButton(formatJson(step.metadata), 'metadata')}
          </div>
          <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto">
            {formatJson(step.metadata)}
          </pre>
        </div>
      )}
    </div>
  );

  // Determine which view to render based on agent type
  let content;
  if (step.agent === 'llm') {
    content = renderLLMDetails();
  } else if (step.agent === 'mcp_tool') {
    content = renderMCPToolDetails();
  } else if (step.agent === 'mcp_resource') {
    content = renderMCPResourceDetails();
  } else {
    content = renderGenericDetails();
  }

  return (
    <div className="px-4 py-4 bg-gray-50 border-t border-gray-200">
      {/* Error section if present */}
      {step.metadata.error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
          <div className="text-sm font-semibold text-red-700 mb-1">⚠️ Error</div>
          <div className="text-xs text-red-900 whitespace-pre-wrap">{step.metadata.error}</div>
        </div>
      )}

      {content}

      {/* Additional metadata at bottom */}
      {Object.keys(step.metadata).length > 0 && (
        <details className="mt-4 text-xs">
          <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
            📋 Full Raw Metadata
          </summary>
          <pre className="mt-2 p-3 bg-white rounded border border-gray-200 overflow-x-auto">
            {formatJson(step.metadata)}
          </pre>
        </details>
      )}
    </div>
  );
}

// ============================================================================
// Execution Result View Component
// ============================================================================

interface ExecutionResultViewProps {
  result: ExecutionResult;
}

function ExecutionResultView({ result }: ExecutionResultViewProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

  const toggleStep = (index: number) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSteps(newExpanded);
  };

  const getStepIcon = (stepType: string) => {
    switch (stepType) {
      case 'thought': return '💭';
      case 'action': return '⚡';
      case 'observation': return '👁️';
      case 'reflection': return '🔍';
      case 'decision': return '🎯';
      default: return '📍';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'green';
      case 'error': return 'red';
      case 'timeout': return 'orange';
      default: return 'gray';
    }
  };

  const color = getStatusColor(result.status);

  return (
    <div className="space-y-4">
      {/* Summary Card */}
      <div className={`bg-white rounded-lg shadow p-6 border-l-4 border-${color}-500`}>
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Execution Result
            </h2>
            <div className="flex items-center gap-4 text-sm">
              <span className={`px-3 py-1 rounded-full bg-${color}-100 text-${color}-700 font-medium`}>
                {result.status.toUpperCase()}
              </span>
              <span className="text-gray-600">
                ⏱️ {result.execution_time.toFixed(2)}s
              </span>
              <span className="text-gray-600">
                📊 {result.steps.length} steps
              </span>
            </div>
          </div>
        </div>

        {/* Final Result */}
        {result.result && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="text-sm font-medium text-gray-700 mb-2">Final Output:</div>
            <div className="text-gray-900 whitespace-pre-wrap">{result.result}</div>
          </div>
        )}

        {/* Error */}
        {result.error && (
          <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
            <div className="text-sm font-medium text-red-700 mb-2">Error:</div>
            <div className="text-red-900 whitespace-pre-wrap">{result.error}</div>
          </div>
        )}
      </div>

      {/* Execution Steps */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Execution Trace ({result.steps.length} steps)
        </h3>

        {result.steps.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No execution steps recorded. The workflow may have failed before logging began.
          </div>
        ) : (
          <div className="space-y-2">
            {result.steps.map((step, index) => (
              <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
                <button
                  onClick={() => toggleStep(index)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{getStepIcon(step.step_type)}</span>
                    <div className="text-left">
                      <div className="font-medium text-gray-900">
                        Step {index + 1}: {step.step_type}
                      </div>
                      <div className="text-sm text-gray-600">
                        {step.agent && `Agent: ${step.agent}`}
                        {step.node_id && ` • Node: ${step.node_id}`}
                        {` • Iteration ${step.iteration}`}
                      </div>
                    </div>
                  </div>
                  <svg
                    className={`w-5 h-5 text-gray-500 transition-transform ${
                      expandedSteps.has(index) ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {expandedSteps.has(index) && (
                  <StepDetailView step={step} />
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Metadata */}
      {Object.keys(result.metadata).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Execution Metadata</h3>
          <pre className="text-sm bg-gray-50 p-4 rounded-lg overflow-x-auto">
            {JSON.stringify(result.metadata, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
