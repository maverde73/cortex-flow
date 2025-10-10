/**
 * Visual workflow editor using React Flow
 */

import { useCallback, useMemo, useEffect, useState } from 'react';
import ReactFlow, {
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
} from 'reactflow';
import type {
  Node,
  Edge,
  Connection,
  NodeTypes,
} from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';

import { AgentNode, StartNode, EndNode, ConditionNode } from './workflow-nodes';
import type { AgentNodeData, ConditionNodeData } from './workflow-nodes';
import type { Workflow, ConditionalEdge } from '../types/api';

interface WorkflowVisualEditorProps {
  workflow: Workflow | null;
  onChange: (workflow: Workflow) => void;
  onSave: () => void;
  onCancel: () => void;
  isLoading?: boolean;
  isSaving?: boolean;
}

// Custom node types
const nodeTypes: NodeTypes = {
  agent: AgentNode,
  start: StartNode,
  end: EndNode,
  condition: ConditionNode,
};

// Format condition label for display
function formatConditionLabel(condition: any): string {
  const field = condition.field.split('.').pop() || condition.field; // Get last part (e.g., "has_error")
  const value = String(condition.value);
  const operator = condition.operator;

  // Common semantic patterns
  if (field === 'has_error' && value === 'false') return 'success';
  if (field === 'has_error' && value === 'true') return 'error';
  if (field === 'quality_score' && operator === '>=') return `quality ≥ ${value}`;
  if (field === 'sentiment_score' && operator === '>') return `positive (> ${value})`;
  if (field === 'sentiment_score' && operator === '<') return `negative (< ${value})`;

  // Operator-specific formatting
  switch (operator) {
    case 'equals':
    case '==':
      if (value === 'true') return field;
      if (value === 'false') return `!${field}`;
      return `${field} = ${value}`;

    case 'not_equals':
    case '!=':
      return `${field} ≠ ${value}`;

    case '>':
      return `${field} > ${value}`;

    case '<':
      return `${field} < ${value}`;

    case '>=':
      return `${field} ≥ ${value}`;

    case '<=':
      return `${field} ≤ ${value}`;

    case 'contains':
      return `${field} ∋ ${value}`;

    case 'not_contains':
      return `${field} ∌ ${value}`;

    case 'in':
      const inValues = Array.isArray(condition.value) ? condition.value.join(', ') : value;
      return `${field} ∈ [${inValues}]`;

    case 'not_in':
      const notInValues = Array.isArray(condition.value) ? condition.value.join(', ') : value;
      return `${field} ∉ [${notInValues}]`;

    default:
      return `${field} ${operator} ${value}`;
  }
}

// Convert workflow to React Flow nodes and edges
function workflowToFlow(workflow: Workflow): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  // Check if this is new format (nodes) or old format (agents)
  if (workflow.nodes && workflow.nodes.length > 0) {
    // New LangGraph format: nodes with depends_on

    // Start node
    nodes.push({
      id: 'start',
      type: 'start',
      position: { x: 0, y: 0 },
      data: {},
    });

    // Convert workflow nodes to React Flow nodes
    workflow.nodes.forEach((node, index) => {
      nodes.push({
        id: node.id,
        type: 'agent',
        position: { x: 0, y: (index + 1) * 150 },
        data: {
          label: node.id,
          type: node.agent,
          enabled: true,
          stepsCount: 1,
          tool_name: node.tool_name,
          parallel_group: node.parallel_group,
          timeout: node.timeout,
          template: node.template,
          instruction: node.instruction,
        } as AgentNodeData,
      });
    });

    // End node
    nodes.push({
      id: 'end',
      type: 'end',
      position: { x: 0, y: (workflow.nodes.length + 1) * 150 },
      data: {},
    });

    // Create edges based on depends_on
    workflow.nodes.forEach((node) => {
      const dependsOn = node.depends_on || [];  // ← Handle undefined/missing depends_on

      if (dependsOn.length === 0) {
        // No dependencies → connect from start
        edges.push({
          id: `start-${node.id}`,
          source: 'start',
          target: node.id,
          type: 'smoothstep',
          animated: true,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 20,
            height: 20,
          },
        });
      } else {
        // Connect from dependencies
        dependsOn.forEach((dep) => {
          edges.push({
            id: `${dep}-${node.id}`,
            source: dep,
            target: node.id,
            type: 'smoothstep',
            animated: true,
            markerEnd: {
              type: MarkerType.ArrowClosed,
              width: 20,
              height: 20,
            },
          });
        });
      }
    });

    // Process conditional edges if present
    if (workflow.conditional_edges && workflow.conditional_edges.length > 0) {
      workflow.conditional_edges.forEach((condEdge) => {
        // Create edges for each condition
        condEdge.conditions.forEach((condition, idx) => {
          edges.push({
            id: `${condEdge.from_node}-${condition.next_node}-condition-${idx}`,
            source: condEdge.from_node,
            target: condition.next_node,
            type: 'smoothstep',
            animated: true,
            label: formatConditionLabel(condition),
            style: { stroke: '#10b981', strokeWidth: 2 }, // Green for success conditions
            labelStyle: { fill: '#10b981', fontWeight: 600, fontSize: 11 },
            labelBgStyle: { fill: '#f0fdf4', fillOpacity: 0.9 },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              width: 20,
              height: 20,
              color: '#10b981',
            },
          });
        });

        // Create default edge (usually error/retry path)
        edges.push({
          id: `${condEdge.from_node}-${condEdge.default}-default`,
          source: condEdge.from_node,
          target: condEdge.default,
          type: 'smoothstep',
          animated: true,
          label: 'retry/error',
          style: { stroke: '#ef4444', strokeWidth: 2, strokeDasharray: '5,5' }, // Red dashed for error
          labelStyle: { fill: '#ef4444', fontWeight: 600, fontSize: 11 },
          labelBgStyle: { fill: '#fef2f2', fillOpacity: 0.9 },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 20,
            height: 20,
            color: '#ef4444',
          },
        });
      });
    }

    // Connect last nodes to end (nodes that have no outgoing edges)
    const nodesWithConditionalEdges = new Set(
      workflow.conditional_edges?.map((ce) => ce.from_node) || []
    );

    const lastNodes = workflow.nodes.filter((node) => {
      // Node is "last" if:
      // 1. No other node depends on it
      // 2. It's not a source of conditional edges
      const noDependents = !workflow.nodes!.some((n) => {
        const deps = n.depends_on || [];  // ← Handle undefined/missing depends_on
        return deps.includes(node.id);
      });
      const noConditionalOut = !nodesWithConditionalEdges.has(node.id);
      return noDependents && noConditionalOut;
    });

    lastNodes.forEach((node) => {
      edges.push({
        id: `${node.id}-end`,
        source: node.id,
        target: 'end',
        type: 'smoothstep',
        animated: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
        },
      });
    });

  } else if (workflow.agents) {
    // Old format: agents with routing

    // Start node
    nodes.push({
      id: 'start',
      type: 'start',
      position: { x: 0, y: 0 },
      data: {},
    });

    // Agent nodes
    let yOffset = 150;
    Object.entries(workflow.agents).forEach(([name, agent]) => {
      const stepsCount = agent.steps?.length || 0;
      nodes.push({
        id: name,
        type: 'agent',
        position: { x: 0, y: yOffset },
        data: {
          label: name,
          type: agent.type,
          enabled: agent.enabled !== false,
          stepsCount,
        } as AgentNodeData,
      });
      yOffset += 150;
    });

    // End node
    nodes.push({
      id: 'end',
      type: 'end',
      position: { x: 0, y: yOffset },
      data: {},
    });

    // Create edges from routing
    if (workflow.routing) {
      Object.entries(workflow.routing).forEach(([from, to]) => {
        edges.push({
          id: `${from}-${to}`,
          source: from,
          target: to,
          type: 'smoothstep',
          animated: true,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 20,
            height: 20,
          },
        });
      });
    }
  }

  return { nodes, edges };
}

// Auto-layout using dagre
function getLayoutedElements(
  nodes: Node[],
  edges: Edge[],
  direction = 'TB'
): { nodes: Node[]; edges: Edge[] } {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 180, height: 80 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 90,
        y: nodeWithPosition.y - 40,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

export function WorkflowVisualEditor({
  workflow,
  onChange,
  onSave,
  onCancel,
  isLoading = false,
  isSaving = false,
}: WorkflowVisualEditorProps) {
  // Convert workflow to flow format
  const initialFlow = useMemo(() => {
    if (!workflow) return { nodes: [], edges: [] };
    const flow = workflowToFlow(workflow);
    return getLayoutedElements(flow.nodes, flow.edges);
  }, [workflow]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialFlow.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialFlow.edges);
  const [lastSyncedWorkflowHash, setLastSyncedWorkflowHash] = useState<string>('');

  // Update nodes and edges when workflow changes from other editors
  useEffect(() => {
    if (workflow) {
      const currentHash = JSON.stringify(workflow);
      // Only update if workflow changed from external source (avoid overwriting user edits)
      if (currentHash !== lastSyncedWorkflowHash) {
        const flow = workflowToFlow(workflow);
        const layouted = getLayoutedElements(flow.nodes, flow.edges);
        setNodes(layouted.nodes);
        setEdges(layouted.edges);
        setLastSyncedWorkflowHash(currentHash);
      }
    }
  }, [workflow, lastSyncedWorkflowHash, setNodes, setEdges]);

  // Handle new connections
  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            type: 'smoothstep',
            animated: true,
            markerEnd: {
              type: MarkerType.ArrowClosed,
            },
          },
          eds
        )
      );
    },
    [setEdges]
  );

  // Auto-layout button handler
  const handleAutoLayout = () => {
    const layouted = getLayoutedElements(nodes, edges);
    setNodes(layouted.nodes);
    setEdges(layouted.edges);
  };

  // Convert flow back to workflow (for saving)
  const handleSave = () => {
    if (!workflow) return;

    // Update routing based on edges
    const newRouting: Record<string, string> = {};
    edges.forEach((edge) => {
      newRouting[edge.source] = edge.target;
    });

    const updatedWorkflow: Workflow = {
      ...workflow,
      routing: newRouting,
    };

    onChange(updatedWorkflow);
    onSave();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-gray-600">Loading workflow...</div>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-gray-600">No workflow selected</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between bg-gray-50 p-3 rounded-lg border">
        <div className="flex items-center gap-2">
          <button
            onClick={handleAutoLayout}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            title="Auto-layout nodes"
          >
            🎨 Auto Layout
          </button>
          <div className="text-sm text-gray-600">
            {nodes.length} nodes, {edges.length} connections
          </div>
        </div>

        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span>Drag nodes • Connect handles • Scroll to zoom</span>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="border rounded-lg overflow-hidden bg-white" style={{ height: '600px' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
          <Controls />
        </ReactFlow>
      </div>

      {/* Info Panel */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <span className="text-blue-600 text-xl">ℹ️</span>
          <div className="flex-1">
            <div className="font-medium text-blue-800">Visual Editor</div>
            <div className="text-sm text-blue-600 mt-1">
              Drag nodes to rearrange, connect handles to create routing, or click "Auto Layout"
              for automatic positioning. Changes to routing will be reflected in the JSON when you
              save.
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-2 border-t">
        <div className="text-sm text-gray-500">
          💡 Tip: Switch between Visual and Code editors to see changes in both views
        </div>

        <div className="flex gap-2">
          <button
            onClick={onCancel}
            disabled={isSaving}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
