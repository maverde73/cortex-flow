# Phase 6 Workflow Visual Editor - Completato ✅

**Data completamento**: 7 Ottobre 2025
**Stato**: Visual workflow editor completo con React Flow, custom nodes, auto-layout, e bi-directional sync

## Riepilogo

La **Fase 6** dell'implementazione del Web Editor è stata completata con successo. Il sistema di editing visuale dei workflow è ora completamente funzionante con React Flow, custom node types (Agent, Start, End, Condition), drag & drop, auto-layout con Dagre, e tab switcher Code ⟺ Visual.

## Features Implementate

### 1. Custom Node Types ✅

Creati 4 tipi di nodi personalizzati per rappresentare diversi elementi del workflow:

#### AgentNode
**File**: `frontend/src/components/workflow-nodes/AgentNode.tsx` (55 righe)

Features:
- Icona robot 🤖
- Label (nome agente)
- Type badge (researcher, analyst, writer, etc.)
- Steps counter
- Enabled/disabled state (opacity 50%)
- Border blu quando selezionato
- Handles: top (target) + bottom (source)

Design:
```tsx
<div className="px-4 py-3 rounded-lg border-2 bg-white shadow-md min-w-[180px]">
  <Handle type="target" position={Position.Top} />
  🤖 {label} ({type})
  {stepsCount} steps
  <Handle type="source" position={Position.Bottom} />
</div>
```

#### StartNode
**File**: `frontend/src/components/workflow-nodes/StartNode.tsx` (30 righe)

Features:
- Gradient green (from-green-400 to-green-500)
- Rounded-full shape
- ▶️ START label
- Handle bottom (source only)
- Scale-105 quando selezionato

#### EndNode
**File**: `frontend/src/components/workflow-nodes/EndNode.tsx` (30 righe)

Features:
- Gradient red (from-red-400 to-red-500)
- Rounded-full shape
- ⏹️ END label
- Handle top (target only)
- Scale-105 quando selezionato

#### ConditionNode
**File**: `frontend/src/components/workflow-nodes/ConditionNode.tsx` (55 righe)

Features:
- Diamond shape (rotate-45)
- Yellow background (bg-yellow-50)
- 🔀 Routing icon
- Label + condition text
- 2 handles output:
  - Right: "true" (green)
  - Bottom: "false" (red)
- Handle top (target)

### 2. WorkflowVisualEditor Component ✅
**File**: `frontend/src/components/WorkflowVisualEditor.tsx` (280 righe)

#### Core Features
- **React Flow canvas** (600px height)
- **Workflow → Flow conversion**:
  ```typescript
  function workflowToFlow(workflow: Workflow): { nodes: Node[]; edges: Edge[] }
  ```
  - Start node (id: 'start')
  - Agent nodes (da workflow.agents)
  - End node (id: 'end')
  - Edges (da workflow.routing)

- **Auto-layout con Dagre**:
  ```typescript
  function getLayoutedElements(nodes, edges, direction = 'TB')
  ```
  - Top-to-Bottom layout
  - 180x80px node size
  - Dagre graph algorithm

- **Interactive features**:
  - Drag nodes
  - Connect handles
  - Zoom (scroll)
  - Pan (drag canvas)
  - Select nodes (border highlight)

- **Toolbar**:
  - 🎨 Auto Layout button
  - Node counter (N nodes, M connections)
  - Help text (Drag nodes • Connect handles • Scroll to zoom)

- **Info panel**:
  - Blue banner con tips
  - Explain visual editor usage

- **Actions**:
  - Cancel button
  - Save Changes button
  - Disabled durante saving

#### React Flow Configuration
```typescript
const nodeTypes: NodeTypes = {
  agent: AgentNode,
  start: StartNode,
  end: EndNode,
  condition: ConditionNode,
};

<ReactFlow
  nodes={nodes}
  edges={edges}
  onNodesChange={onNodesChange}
  onEdgesChange={onEdgesChange}
  onConnect={onConnect}
  nodeTypes={nodeTypes}
  fitView
>
  <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
  <Controls />
</ReactFlow>
```

#### Edge Styling
- Type: `smoothstep`
- Animated: `true`
- Marker: `ArrowClosed` (20x20px)
- Color: Default blue

### 3. WorkflowsPage Integration ✅
**File**: `frontend/src/pages/WorkflowsPage.tsx` (modificato)

#### Tab Switcher (Code ⟺ Visual)
```tsx
<div className="flex rounded-lg border border-gray-300 bg-gray-50 p-1">
  <button onClick={() => setEditorMode('code')}>
    📝 Code
  </button>
  <button onClick={() => setEditorMode('visual')}>
    🎨 Visual
  </button>
</div>
```

Design:
- Rounded-lg container con border
- Gray-50 background
- Active button: white bg + blue text + shadow
- Inactive button: gray text + hover effect
- Smooth transitions

#### Conditional Rendering
```tsx
{editorMode === 'code' ? (
  <WorkflowCodeEditor ... />
) : (
  <WorkflowVisualEditor ... />
)}
```

#### State Management
- `editorMode`: 'code' | 'visual'
- Default: 'code'
- Persiste durante edit session
- Reset quando torna a list mode

### 4. Bi-directional Sync ✅

#### Workflow → Visual
- `workflowToFlow()` converte JSON → React Flow format
- Chiamato in `useMemo()` quando workflow cambia
- Auto-layout applicato ai nodi

#### Visual → Workflow
- User modifica posizioni nodi (drag)
- User crea/elimina connessioni (handles)
- `handleSave()` converte edges → routing
- Aggiorna workflow.routing:
  ```typescript
  edges.forEach((edge) => {
    newRouting[edge.source] = edge.target;
  });
  ```

#### Sync Strategy
- **One-way per posizioni**: Posizioni nodi non salvate in JSON
- **Bi-directional per routing**: Edges ⟺ workflow.routing
- **Preserve agents data**: Agents config non modificato da visual editor

## Architettura

### Component Tree
```
WorkflowsPage
├── Header
│   └── Tab Switcher: 📝 Code | 🎨 Visual
└── Content (conditional)
    ├── Code Mode
    │   └── WorkflowCodeEditor
    │       └── Monaco Editor
    └── Visual Mode
        └── WorkflowVisualEditor
            ├── Toolbar (auto-layout, counters)
            ├── ReactFlow Canvas
            │   ├── Background (dots)
            │   ├── Controls (zoom, fit)
            │   ├── Nodes (custom types)
            │   └── Edges (smoothstep, animated)
            ├── Info Panel (tips)
            └── Actions (save, cancel)
```

### Data Flow
```
1. User clicks workflow → Edit mode
   └→ Fetch workflow JSON
   └→ Set editedWorkflow state
   └→ Default: editorMode = 'code'

2. User clicks "🎨 Visual" tab
   └→ setEditorMode('visual')
   └→ WorkflowVisualEditor renders
   └→ workflowToFlow(editedWorkflow)
   └→ getLayoutedElements(nodes, edges)
   └→ ReactFlow displays canvas

3. User drags nodes, connects handles
   └→ onNodesChange → setNodes (local)
   └→ onEdgesChange → setEdges (local)
   └→ onConnect → addEdge (local)

4. User clicks "Save Changes"
   └→ Convert edges → routing
   └→ Update editedWorkflow.routing
   └→ Call onChange(updatedWorkflow)
   └→ Call onSave() → PUT API
   └→ Invalidate queries

5. User switches to "📝 Code" tab
   └→ setEditorMode('code')
   └→ Monaco shows updated JSON (routing changed)
```

## Dependencies Installate

### React Flow
```bash
npm install reactflow
```
- **Versione**: ~11.x
- **Bundle size**: ~200KB gzipped
- **Features used**:
  - ReactFlow component
  - useNodesState, useEdgesState hooks
  - Background, Controls
  - Custom node types
  - Smooth step edges
  - Animated edges
  - Markers (arrows)

### Dagre
```bash
npm install dagre @types/dagre
```
- **Versione**: ~0.8.x
- **Purpose**: Auto-layout algorithm
- **Usage**: Top-to-bottom hierarchical layout

## Test Effettuati

### ✅ Visual Editor Rendering
- ✅ Open workflow → Click "🎨 Visual" → Canvas renders
- ✅ Start node (green, rounded)
- ✅ Agent nodes (white, rounded-lg, 🤖 icon)
- ✅ End node (red, rounded)
- ✅ Edges (smoothstep, animated, arrows)

### ✅ Interactions
- ✅ Drag nodes → Position updates
- ✅ Click node → Border blue (selected)
- ✅ Scroll canvas → Zoom in/out
- ✅ Drag canvas → Pan view
- ✅ Click handle → Connect mode
- ✅ Drop on handle → Edge created
- ✅ Click edge → Selected
- ✅ Delete key → Remove selected edge/node

### ✅ Auto-layout
- ✅ Click "🎨 Auto Layout" → Nodes rearrange
- ✅ Top-to-bottom flow
- ✅ No overlaps
- ✅ Consistent spacing

### ✅ Tab Switching
- ✅ Start in Code mode → Monaco visible
- ✅ Switch to Visual → Canvas visible
- ✅ Switch back to Code → Monaco visible
- ✅ Active tab: white bg + shadow
- ✅ Inactive tab: gray text

### ✅ Save Flow
- ✅ Modify connections in visual
- ✅ Click "Save Changes"
- ✅ API PUT called
- ✅ Return to list mode
- ✅ Re-open workflow → Changes persisted
- ✅ Switch to Code → JSON routing updated

## File Creati/Modificati

### Nuovi File (6)
1. `frontend/src/components/workflow-nodes/AgentNode.tsx` (55 righe)
2. `frontend/src/components/workflow-nodes/StartNode.tsx` (30 righe)
3. `frontend/src/components/workflow-nodes/EndNode.tsx` (30 righe)
4. `frontend/src/components/workflow-nodes/ConditionNode.tsx` (55 righe)
5. `frontend/src/components/workflow-nodes/index.ts` (10 righe)
6. `frontend/src/components/WorkflowVisualEditor.tsx` (280 righe)

### File Modificati (2)
1. `frontend/src/pages/WorkflowsPage.tsx` (300+ righe)
   - Import WorkflowVisualEditor
   - State editorMode
   - Tab switcher UI
   - Conditional rendering

2. `frontend/package.json`
   - Added: reactflow
   - Added: dagre
   - Added: @types/dagre

### Totale nuovo codice: ~460 righe

## UX Features

### Visual Design
- **Node colors**:
  - Start: Green gradient
  - End: Red gradient
  - Agent: White with blue border
  - Condition: Yellow diamond
- **Icons**: 🤖 (agent), ▶️ (start), ⏹️ (end), 🔀 (condition)
- **Shadows**: md (nodes), lg (selected)
- **Borders**: 2px solid, blue when selected
- **Animations**: Edge flow, scale on select

### Interactive Feedback
- **Hover effects**: Border color change
- **Selected state**: Border blue + shadow-lg
- **Connection mode**: Handles highlight
- **Zoom indicator**: Controls bottom-right
- **Fit view**: Auto-zoom to fit all nodes

### Keyboard Support (React Flow Built-in)
- `Ctrl/Cmd + Scroll`: Zoom
- `Delete/Backspace`: Remove selected
- `Ctrl/Cmd + A`: Select all
- `Ctrl/Cmd + C/V`: Copy/paste (nodes)

### Toolbar Actions
- 🎨 Auto Layout: Re-arrange nodes
- Counter: X nodes, Y connections
- Help text: Usage instructions

## Limitazioni Attuali

### 1. No Node Creation from Palette ❌
- Cannot add new agent nodes
- Only modify existing workflow
- **Workaround**: Add agent in Code mode first

### 2. No Node Properties Panel ❌
- Cannot edit agent config in visual mode
- No inline editor for steps
- **Workaround**: Switch to Code mode

### 3. No Condition Node Creation ❌
- Routing is simple: A → B
- No if/else logic in visual mode
- **Future**: Add condition nodes from palette

### 4. No MCP Nodes ❌
- No visual representation of MCP servers
- **Future**: Add MCP node type

### 5. Node Positions Not Persisted ❌
- Layout reset ogni reload
- Auto-layout ogni volta
- **Future**: Save node positions in workflow metadata

### 6. No Undo/Redo ❌
- No history for node moves
- **Workaround**: Cancel to reset

## Miglioramenti Futuri

### UX
- [ ] Node palette sidebar (drag to add)
- [ ] Properties panel (edit agent config)
- [ ] Double-click node → edit inline
- [ ] Right-click context menu
- [ ] Copy/paste nodes
- [ ] Duplicate node
- [ ] Search nodes
- [ ] Minimap toggle
- [ ] Grid snap
- [ ] Alignment guides

### Node Types
- [ ] MCP node (purple, 🔌 icon)
- [ ] Parallel node (⚡ fork/join)
- [ ] Loop node (🔄 repeat)
- [ ] Comment node (📝 annotation)

### Layout
- [ ] Save node positions in metadata
- [ ] Multiple layout algorithms (LR, RL, BT)
- [ ] Manual layout lock
- [ ] Compact mode (smaller nodes)

### Validation
- [ ] Visual error indicators (red borders)
- [ ] Dead-end detection (highlight)
- [ ] Circular dependency warning
- [ ] Unreachable nodes highlight

### Collaboration
- [ ] Real-time cursors (multi-user)
- [ ] Comments on nodes
- [ ] Version diff (show changes visually)

## Integrazione con Altre Fasi

### Fase 4: Code Editor
- ✅ Tab switcher: Code ⟺ Visual
- ✅ Bi-directional sync (routing)
- ✅ Same save/cancel logic

### Fase 5: AI Generation
- ✅ Generate workflow → Open visual editor
- ✅ Preview AI-generated flow visually
- **Future**: Generate visual layout from description

### Fase 8: Testing
- Visual execution trace (highlight active node)
- Step-through debugger in visual mode
- Error indicators on failed nodes

## Comandi Utili

### Test Visual Editor
```bash
# Frontend
cd /home/mverde/src/taal/mcp-servers/cortex-flow/frontend
npm run dev

# Visit
http://localhost:5173/workflows

# Steps:
1. Click any workflow
2. Click "🎨 Visual" tab
3. Drag nodes
4. Connect handles
5. Click "🎨 Auto Layout"
6. Click "Save Changes"
7. Switch to "📝 Code" → See routing updated
```

### Install Dependencies
```bash
cd frontend
npm install reactflow dagre @types/dagre
```

### Check Bundle Size
```bash
cd frontend
npm run build
du -sh dist/  # Should be ~600KB (with Monaco + React Flow)
```

## Note Tecniche

### React Flow Performance
- **Lazy rendering**: Only visible nodes rendered
- **Virtualization**: Off-screen nodes not in DOM
- **Memo**: All node components memoized
- **Bundle**: Separate chunk (lazy-loaded)

### Dagre Layout Algorithm
- **Time complexity**: O(V + E) where V=nodes, E=edges
- **Strategy**: Rank assignment → Node ordering → Positioning
- **Result**: Hierarchical layout with minimal edge crossings

### State Management
```typescript
// React Flow hooks
const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

// Sync strategy
useMemo(() => {
  if (!workflow) return { nodes: [], edges: [] };
  const flow = workflowToFlow(workflow);
  return getLayoutedElements(flow.nodes, flow.edges);
}, [workflow]);  // Re-compute quando workflow cambia
```

### Edge Creation
```typescript
const onConnect = useCallback((connection: Connection) => {
  setEdges((eds) => addEdge({
    ...connection,
    type: 'smoothstep',
    animated: true,
    markerEnd: { type: MarkerType.ArrowClosed },
  }, eds));
}, [setEdges]);
```

## Problemi Risolti

### ✅ Dagre Layout Crashes
**Issue**: Dagre throws error on empty graph
**Fix**: Check nodes.length > 0 before layout

### ✅ Node Positions Reset
**Issue**: Positions lost on re-render
**Fix**: useMemo to preserve initial layout

### ✅ Edges Not Animated
**Issue**: Static edges
**Fix**: Set `animated: true` in edge config

### ✅ Handles Not Clickable
**Issue**: Cannot connect nodes
**Fix**: Ensure Handle component not covered by parent

### ✅ Tab Switcher Not Highlighting
**Issue**: Active tab not visible
**Fix**: Add white bg + shadow to active button

## Conclusione

La Fase 6 è completa! Il workflow visual editor è ora funzionante con:
- ✅ React Flow canvas (600px, interactive)
- ✅ Custom node types (Agent, Start, End, Condition)
- ✅ Auto-layout con Dagre (TB)
- ✅ Drag & drop, zoom, pan
- ✅ Connect handles (routing)
- ✅ Tab switcher Code ⟺ Visual
- ✅ Bi-directional sync (routing)
- ✅ Save/cancel actions
- ✅ Info panel e toolbar

**Frontend**: http://localhost:5173/workflows → Open workflow → "🎨 Visual"

**Next**: Fase 7 - MCP Integration (registry browsing, server config)
