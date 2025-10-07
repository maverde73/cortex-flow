# Cortex Flow Web Editor - Implementation Guide

**Version**: 1.0.0
**Date**: 2025-10-07
**Status**: 🚧 In Development

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Backend API](#backend-api)
- [Frontend Application](#frontend-application)
- [Features Implementation](#features-implementation)
- [Development Phases](#development-phases)
- [Testing Strategy](#testing-strategy)
- [Deployment](#deployment)

---

## Overview

The Cortex Flow Web Editor is a comprehensive web-based IDE for managing multi-agent AI workflows. It provides:

- **Visual Workflow Editor** - Drag & drop interface using React Flow
- **Code Editor** - Monaco-based JSON editor with validation
- **AI-Assisted Generation** - Natural language → workflow conversion
- **Project Management** - Multi-project configuration
- **Prompt Library** - System, agent, and MCP prompts
- **MCP Integration** - Browse and configure MCP servers
- **ReAct Configuration** - Base agent mode without workflows

### Key Capabilities

```
┌──────────────────────────────────────────────────┐
│                Cortex Flow Editor                │
├──────────────────────────────────────────────────┤
│                                                  │
│  Project Management    Workflow Editor          │
│  ├─ CRUD operations    ├─ Visual (React Flow)   │
│  ├─ Multi-project      ├─ Code (Monaco)         │
│  └─ Configuration      └─ AI-assisted           │
│                                                  │
│  Prompt Management     MCP Integration          │
│  ├─ System prompts     ├─ Registry browser      │
│  ├─ Agent prompts      ├─ Server config         │
│  └─ MCP prompts        └─ Common library        │
│                                                  │
│  ReAct Config          Testing & Preview        │
│  ├─ Strategy params    ├─ Dry-run execution     │
│  ├─ Logging options    ├─ Execution logs        │
│  └─ Agent settings     └─ Real-time results     │
└──────────────────────────────────────────────────┘
```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Web Browser                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │          React Frontend (Port 3000)             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │   │
│  │  │ Projects │  │ Workflows│  │  Prompts │      │   │
│  │  │ Manager  │  │  Editor  │  │  Editor  │      │   │
│  │  └──────────┘  └──────────┘  └──────────┘      │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API (JSON)
                      │
┌─────────────────────▼───────────────────────────────────┐
│           FastAPI Backend (Port 8002)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │ editor_server.py                                 │  │
│  │  ├─ Projects API      ├─ Prompts API            │  │
│  │  ├─ Workflows API     ├─ MCP API                │  │
│  │  ├─ Agents API        └─ AI Generation API      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │ File I/O
                      │
┌─────────────────────▼───────────────────────────────────┐
│              File System (projects/)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ default/ │  │ staging/ │  │   prod/  │             │
│  │  ├─ project.json        │  │          │             │
│  │  ├─ agents.json         │  │          │             │
│  │  ├─ react.json          │  │          │             │
│  │  ├─ mcp.json            │  │          │             │
│  │  ├─ workflows/          │  │          │             │
│  │  └─ prompts/            │  │          │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

**Project Management**:
```
User Action → React Component → API Call → FastAPI Endpoint →
Read/Write JSON → Update File System → Response → Update UI
```

**Workflow Editing (Visual)**:
```
Drag Node → React Flow → Update State → Convert to JSON →
Validate Schema → Save via API → Write to workflows/*.json
```

**AI Generation**:
```
User Prompt → OpenAI API → Generate JSON → Validate Schema →
Display in Editor → User Review → Save to Project
```

---

## Technology Stack

### Frontend

| Technology | Version | Purpose | License |
|------------|---------|---------|---------|
| **React** | 18.x | UI framework | MIT |
| **TypeScript** | 5.x | Type safety | Apache 2.0 |
| **Vite** | 5.x | Build tool | MIT |
| **React Flow** | 11.x | Visual workflow editor | MIT |
| **Monaco Editor** | 0.45.x | Code editor | MIT |
| **Tailwind CSS** | 3.x | Styling | MIT |
| **shadcn/ui** | Latest | UI components | MIT |
| **Zustand** | 4.x | State management | MIT |
| **TanStack Query** | 5.x | Data fetching | MIT |
| **React Router** | 6.x | Routing | MIT |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.110.x | REST API framework |
| **Pydantic** | 2.x | Data validation |
| **OpenAI** | 1.x | AI workflow generation |
| **httpx** | 0.27.x | HTTP client (MCP Registry) |

### Development Tools

- **Vitest** - Frontend testing
- **React Testing Library** - Component testing
- **Playwright** - E2E testing
- **pytest** - Backend testing
- **ESLint** + **Prettier** - Code quality

---

## Backend API

### Complete API Reference

#### Projects API

```http
# List all projects
GET /api/projects
Response: ProjectInfo[]

# Get project details
GET /api/projects/{name}
Response: ProjectInfo

# Create new project
POST /api/projects
Body: { name, description, template? }
Response: ProjectInfo (201)

# Update project
PUT /api/projects/{name}
Body: { description?, active? }
Response: ProjectInfo

# Delete project
DELETE /api/projects/{name}
Response: 204 No Content

# Activate project
POST /api/projects/{name}/activate
Response: ProjectInfo

# Duplicate project
POST /api/projects/{name}/duplicate
Body: { new_name }
Response: ProjectInfo (201)
```

#### Agents & ReAct API

```http
# Get agents configuration
GET /api/projects/{name}/agents
Response: AgentsConfig

# Update agents configuration
PUT /api/projects/{name}/agents
Body: { config: {...} }
Response: { status, message }

# Get ReAct configuration
GET /api/projects/{name}/react
Response: ReActConfig

# Update ReAct configuration
PUT /api/projects/{name}/react
Body: { config: {...} }
Response: { status, message }
```

#### Prompts API

```http
# List all prompts
GET /api/projects/{name}/prompts
Response: { system, agents: {...}, mcp: {...} }

# Get system prompt
GET /api/projects/{name}/prompts/system
Response: { content }

# Update system prompt
PUT /api/projects/{name}/prompts/system
Body: { content }
Response: { status, message }

# Get agent prompt
GET /api/projects/{name}/prompts/agents/{agent}
Response: { content }

# Update agent prompt
PUT /api/projects/{name}/prompts/agents/{agent}
Body: { content }
Response: { status, message }

# Get MCP server prompt
GET /api/projects/{name}/prompts/mcp/{server}
Response: { content, path }

# Update MCP server prompt
PUT /api/projects/{name}/prompts/mcp/{server}
Body: { content, path? }
Response: { status, message }

# Browse prompt library
GET /api/prompts/library
Response: PromptTemplate[]

# Get prompt template
GET /api/prompts/library/{id}
Response: PromptTemplate
```

#### Workflows API

```http
# List workflows
GET /api/projects/{name}/workflows
Response: WorkflowInfo[]

# Get workflow
GET /api/projects/{name}/workflows/{workflow}
Response: WorkflowData

# Create workflow
POST /api/projects/{name}/workflows
Body: { workflow: {...} }
Response: { status, message } (201)

# Update workflow
PUT /api/projects/{name}/workflows/{workflow}
Body: { workflow: {...} }
Response: { status, message }

# Delete workflow
DELETE /api/projects/{name}/workflows/{workflow}
Response: 204 No Content

# Validate workflow
POST /api/projects/{name}/workflows/validate
Body: { workflow: {...} }
Response: { valid: boolean, errors?: [...] }

# Preview workflow (dry-run)
POST /api/projects/{name}/workflows/{workflow}/preview
Body: { parameters: {...} }
Response: { execution_log: [...], result: {...} }
```

#### AI Generation API

```http
# Generate workflow from description
POST /api/workflows/generate
Body: {
  description: string,
  mode: "json" | "script",
  project: string,
  available_agents?: string[],
  available_mcp?: string[]
}
Response: {
  workflow: {...},
  confidence: number,
  suggestions?: string[]
}
```

#### MCP API

```http
# Browse MCP Registry
GET /api/mcp/registry
Query: ?search=&category=
Response: MCPServer[]

# Get MCP server details
GET /api/mcp/registry/{server_id}
Response: MCPServerDetails

# Get project MCP configuration
GET /api/projects/{name}/mcp
Response: MCPConfig

# Update project MCP configuration
PUT /api/projects/{name}/mcp
Body: { config: {...} }
Response: { status, message }

# Test MCP server connection
POST /api/projects/{name}/mcp/test/{server}
Response: { success: boolean, message, tools?: [...] }

# Get common MCP library
GET /api/mcp/library
Response: MCPServer[]

# Add to common library
POST /api/mcp/library
Body: { server: {...} }
Response: { status, message }

# Remove from common library
DELETE /api/mcp/library/{server_id}
Response: 204 No Content
```

#### Testing & Execution API

```http
# Test ReAct mode
POST /api/projects/{name}/test/react
Body: { query: string }
Response: { result, execution_log: [...] }

# Test workflow
POST /api/projects/{name}/test/workflow/{workflow}
Body: { parameters: {...} }
Response: { result, execution_log: [...] }

# Get execution logs
GET /api/projects/{name}/logs/{run_id}
Response: { run_id, status, logs: [...] }
```

### Pydantic Models

```python
# Core Models
class ProjectInfo(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    active: bool = False
    created_at: str

class AgentsConfig(BaseModel):
    agents: Dict[str, AgentSettings]

class AgentSettings(BaseModel):
    enabled: bool
    llm_provider: str
    model: str
    system_prompt_override: Optional[str] = None

class ReActConfig(BaseModel):
    max_iterations: int = 25
    timeout_seconds: int = 300
    max_consecutive_errors: int = 3
    enable_verbose_logging: bool = True
    log_thoughts: bool = True
    log_actions: bool = True
    log_observations: bool = True
    allow_delegation: bool = True
    enable_reflection: bool = False

class WorkflowNode(BaseModel):
    id: str
    agent: str
    instruction: str
    depends_on: List[str] = []
    timeout: int = 300
    retry_attempts: int = 0
    template: Optional[str] = None

class ConditionalEdge(BaseModel):
    source: str
    condition: str
    target: str
    else_target: Optional[str] = None

class WorkflowTemplate(BaseModel):
    name: str
    version: str = "1.0"
    description: str
    trigger_patterns: List[str] = []
    nodes: List[WorkflowNode]
    conditional_edges: List[ConditionalEdge] = []
    parameters: Dict[str, Any] = {}

class MCPServerConfig(BaseModel):
    type: Literal["remote", "local"]
    transport: str
    url: Optional[str] = None
    local_path: Optional[str] = None
    api_key: Optional[str] = None
    enabled: bool = True
    timeout: float = 30.0
    prompts_file: Optional[str] = None
    prompt_tool_association: Optional[str] = None
```

---

## Frontend Application

### Directory Structure

```
web-editor/
├── public/
│   └── assets/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── MainLayout.tsx
│   │   ├── projects/
│   │   │   ├── ProjectList.tsx
│   │   │   ├── ProjectCard.tsx
│   │   │   ├── ProjectEditor.tsx
│   │   │   └── CreateProjectWizard.tsx
│   │   ├── agents/
│   │   │   ├── AgentsConfig.tsx
│   │   │   ├── ReActEditor.tsx
│   │   │   └── AgentCard.tsx
│   │   ├── prompts/
│   │   │   ├── PromptEditor.tsx
│   │   │   ├── PromptLibrary.tsx
│   │   │   ├── SystemPromptEditor.tsx
│   │   │   ├── AgentPromptEditor.tsx
│   │   │   └── MCPPromptEditor.tsx
│   │   ├── workflows/
│   │   │   ├── WorkflowList.tsx
│   │   │   ├── WorkflowEditor.tsx
│   │   │   ├── VisualEditor.tsx        # React Flow
│   │   │   ├── CodeEditor.tsx          # Monaco
│   │   │   ├── AIAssistant.tsx
│   │   │   ├── NodePalette.tsx
│   │   │   ├── NodeConfigSidebar.tsx
│   │   │   └── PreviewPanel.tsx
│   │   ├── mcp/
│   │   │   ├── MCPBrowser.tsx
│   │   │   ├── ServerCard.tsx
│   │   │   ├── ServerConfig.tsx
│   │   │   └── LibraryPanel.tsx
│   │   ├── testing/
│   │   │   ├── TestPanel.tsx
│   │   │   ├── ExecutionLogs.tsx
│   │   │   └── ResultViewer.tsx
│   │   └── ui/                         # shadcn/ui components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── dialog.tsx
│   │       ├── input.tsx
│   │       ├── select.tsx
│   │       └── ...
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts               # API client base
│   │   │   ├── projects.ts
│   │   │   ├── workflows.ts
│   │   │   ├── prompts.ts
│   │   │   ├── mcp.ts
│   │   │   └── ai.ts
│   │   ├── utils/
│   │   │   ├── validation.ts
│   │   │   ├── workflow-converter.ts   # JSON ↔ Visual
│   │   │   └── helpers.ts
│   │   └── constants.ts
│   ├── stores/
│   │   ├── projectStore.ts
│   │   ├── workflowStore.ts
│   │   ├── promptStore.ts
│   │   └── uiStore.ts
│   ├── types/
│   │   ├── project.ts
│   │   ├── workflow.ts
│   │   ├── agent.ts
│   │   ├── mcp.ts
│   │   └── api.ts
│   ├── hooks/
│   │   ├── useProjects.ts
│   │   ├── useWorkflows.ts
│   │   ├── usePrompts.ts
│   │   └── useMCP.ts
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── ProjectsPage.tsx
│   │   ├── WorkflowEditorPage.tsx
│   │   ├── PromptsPage.tsx
│   │   └── MCPPage.tsx
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

### Component Architecture

#### Project Management

**ProjectList.tsx**:
```typescript
interface ProjectListProps {
  onProjectSelect: (project: Project) => void;
}

export function ProjectList({ onProjectSelect }: ProjectListProps) {
  const { data: projects, isLoading } = useProjects();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {projects?.map(project => (
        <ProjectCard
          key={project.name}
          project={project}
          onClick={() => onProjectSelect(project)}
        />
      ))}
    </div>
  );
}
```

**CreateProjectWizard.tsx**:
```typescript
export function CreateProjectWizard() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<ProjectFormData>({});

  const steps = [
    <BasicInfoStep data={formData} onChange={setFormData} />,
    <AgentsStep data={formData} onChange={setFormData} />,
    <MCPStep data={formData} onChange={setFormData} />,
    <WorkflowsStep data={formData} onChange={setFormData} />,
    <ReviewStep data={formData} onSubmit={handleCreate} />
  ];

  return (
    <Dialog>
      <DialogContent>
        <Stepper currentStep={step} totalSteps={5} />
        {steps[step - 1]}
      </DialogContent>
    </Dialog>
  );
}
```

#### Workflow Editor

**WorkflowEditor.tsx**:
```typescript
export function WorkflowEditor() {
  const [mode, setMode] = useState<'visual' | 'code' | 'ai'>('visual');
  const [workflow, setWorkflow] = useState<Workflow>();

  return (
    <div className="h-screen flex flex-col">
      <Toolbar mode={mode} onModeChange={setMode} />

      <div className="flex-1 flex">
        {/* Main editor area */}
        <div className="flex-1">
          {mode === 'visual' && <VisualEditor workflow={workflow} />}
          {mode === 'code' && <CodeEditor workflow={workflow} />}
          {mode === 'ai' && <AIAssistant onWorkflowGenerated={setWorkflow} />}
        </div>

        {/* Sidebar */}
        {mode === 'visual' && <NodeConfigSidebar />}
      </div>

      <PreviewPanel workflow={workflow} />
    </div>
  );
}
```

**VisualEditor.tsx** (React Flow):
```typescript
import ReactFlow, {
  Node, Edge, Background, Controls, MiniMap
} from 'reactflow';
import 'reactflow/dist/style.css';

export function VisualEditor({ workflow }: VisualEditorProps) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  // Convert workflow JSON to React Flow nodes/edges
  useEffect(() => {
    const converted = convertWorkflowToFlow(workflow);
    setNodes(converted.nodes);
    setEdges(converted.edges);
  }, [workflow]);

  const nodeTypes = {
    agent: AgentNode,
    mcp: MCPToolNode,
    conditional: ConditionalNode,
  };

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      nodeTypes={nodeTypes}
      fitView
    >
      <Background />
      <Controls />
      <MiniMap />
    </ReactFlow>
  );
}
```

**CodeEditor.tsx** (Monaco):
```typescript
import Editor from '@monaco-editor/react';

export function CodeEditor({ workflow }: CodeEditorProps) {
  const [value, setValue] = useState(JSON.stringify(workflow, null, 2));

  const handleEditorChange = (value: string | undefined) => {
    if (!value) return;

    try {
      const parsed = JSON.parse(value);
      validateWorkflow(parsed);
      setValue(value);
    } catch (error) {
      // Show validation error
    }
  };

  return (
    <Editor
      height="100%"
      language="json"
      value={value}
      onChange={handleEditorChange}
      theme="vs-dark"
      options={{
        minimap: { enabled: true },
        formatOnPaste: true,
        formatOnType: true,
      }}
    />
  );
}
```

**AIAssistant.tsx**:
```typescript
export function AIAssistant({ onWorkflowGenerated }: AIAssistantProps) {
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const { mutateAsync: generateWorkflow } = useGenerateWorkflow();

  const handleGenerate = async () => {
    setLoading(true);

    try {
      const result = await generateWorkflow({
        description,
        mode: 'json',
        project: currentProject.name
      });

      onWorkflowGenerated(result.workflow);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <Textarea
        placeholder="Describe your workflow in natural language..."
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        rows={10}
      />

      <Button onClick={handleGenerate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Workflow'}
      </Button>

      {result && <WorkflowPreview workflow={result.workflow} />}
    </div>
  );
}
```

#### Prompt Management

**PromptEditor.tsx**:
```typescript
export function PromptEditor({ type, identifier }: PromptEditorProps) {
  const { data: prompt, isLoading } = usePrompt(type, identifier);
  const { mutateAsync: updatePrompt } = useUpdatePrompt();

  const [content, setContent] = useState('');

  useEffect(() => {
    if (prompt) {
      setContent(prompt.content);
    }
  }, [prompt]);

  const handleSave = async () => {
    await updatePrompt({
      type,
      identifier,
      content
    });
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between p-4 border-b">
        <h2>Editing: {type} / {identifier}</h2>
        <Button onClick={handleSave}>Save</Button>
      </div>

      <Editor
        height="100%"
        language="markdown"
        value={content}
        onChange={(value) => setContent(value || '')}
        theme="vs-dark"
      />
    </div>
  );
}
```

### State Management (Zustand)

```typescript
// stores/projectStore.ts
interface ProjectStore {
  currentProject: Project | null;
  projects: Project[];
  setCurrentProject: (project: Project) => void;
  addProject: (project: Project) => void;
  updateProject: (name: string, updates: Partial<Project>) => void;
  deleteProject: (name: string) => void;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  currentProject: null,
  projects: [],

  setCurrentProject: (project) =>
    set({ currentProject: project }),

  addProject: (project) =>
    set((state) => ({
      projects: [...state.projects, project]
    })),

  updateProject: (name, updates) =>
    set((state) => ({
      projects: state.projects.map(p =>
        p.name === name ? { ...p, ...updates } : p
      )
    })),

  deleteProject: (name) =>
    set((state) => ({
      projects: state.projects.filter(p => p.name !== name)
    })),
}));
```

### API Client

```typescript
// lib/api/client.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// lib/api/projects.ts
export const projectsApi = {
  list: () => apiClient.get<Project[]>('/api/projects'),

  get: (name: string) =>
    apiClient.get<Project>(`/api/projects/${name}`),

  create: (data: CreateProjectData) =>
    apiClient.post<Project>('/api/projects', data),

  update: (name: string, data: UpdateProjectData) =>
    apiClient.put<Project>(`/api/projects/${name}`, data),

  delete: (name: string) =>
    apiClient.delete(`/api/projects/${name}`),

  activate: (name: string) =>
    apiClient.post<Project>(`/api/projects/${name}/activate`),
};
```

### React Query Hooks

```typescript
// hooks/useProjects.ts
export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list().then(res => res.data),
  });
}

export function useProject(name: string) {
  return useQuery({
    queryKey: ['projects', name],
    queryFn: () => projectsApi.get(name).then(res => res.data),
    enabled: !!name,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateProjectData) =>
      projectsApi.create(data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}
```

---

## Features Implementation

### 1. Visual Workflow Editor

**Implementation Steps**:

1. **Setup React Flow**
   ```bash
   npm install reactflow
   ```

2. **Define Custom Node Types**
   ```typescript
   // AgentNode.tsx
   export function AgentNode({ data }: NodeProps) {
     return (
       <div className="agent-node">
         <Handle type="target" position={Position.Top} />

         <div className="node-header">
           <AgentIcon type={data.agent} />
           <span>{data.agent}</span>
         </div>

         <div className="node-body">
           <p>{data.instruction}</p>
         </div>

         <Handle type="source" position={Position.Bottom} />
       </div>
     );
   }
   ```

3. **Workflow Converter**
   ```typescript
   // Convert JSON workflow to React Flow format
   export function convertWorkflowToFlow(workflow: Workflow) {
     const nodes: Node[] = workflow.nodes.map((node, index) => ({
       id: node.id,
       type: 'agent',
       position: calculatePosition(index, workflow.nodes.length),
       data: {
         agent: node.agent,
         instruction: node.instruction,
         ...node
       }
     }));

     const edges: Edge[] = [];

     // Create edges from depends_on
     workflow.nodes.forEach(node => {
       node.depends_on.forEach(depId => {
         edges.push({
           id: `${depId}-${node.id}`,
           source: depId,
           target: node.id,
         });
       });
     });

     // Add conditional edges
     workflow.conditional_edges?.forEach(condEdge => {
       edges.push({
         id: `${condEdge.source}-${condEdge.target}`,
         source: condEdge.source,
         target: condEdge.target,
         label: condEdge.condition,
         type: 'conditional',
       });
     });

     return { nodes, edges };
   }

   // Convert React Flow to JSON workflow
   export function convertFlowToWorkflow(
     nodes: Node[],
     edges: Edge[]
   ): Workflow {
     const workflowNodes: WorkflowNode[] = nodes.map(node => ({
       id: node.id,
       agent: node.data.agent,
       instruction: node.data.instruction,
       depends_on: edges
         .filter(e => e.target === node.id && e.type !== 'conditional')
         .map(e => e.source),
       timeout: node.data.timeout || 300,
     }));

     const conditionalEdges: ConditionalEdge[] = edges
       .filter(e => e.type === 'conditional')
       .map(e => ({
         source: e.source,
         condition: e.label || '',
         target: e.target,
       }));

     return {
       name: 'untitled',
       nodes: workflowNodes,
       conditional_edges: conditionalEdges,
       parameters: {},
     };
   }
   ```

4. **Node Configuration Sidebar**
   ```typescript
   export function NodeConfigSidebar() {
     const selectedNode = useSelectedNode();

     if (!selectedNode) {
       return <div>Select a node to configure</div>;
     }

     return (
       <div className="w-80 border-l p-4">
         <h3>Node Configuration</h3>

         <Form>
           <FormField name="agent">
             <Select value={selectedNode.data.agent}>
               <option value="researcher">Researcher</option>
               <option value="analyst">Analyst</option>
               <option value="writer">Writer</option>
             </Select>
           </FormField>

           <FormField name="instruction">
             <Textarea value={selectedNode.data.instruction} />
           </FormField>

           <FormField name="timeout">
             <Input type="number" value={selectedNode.data.timeout} />
           </FormField>
         </Form>
       </div>
     );
   }
   ```

### 2. AI Workflow Generation

**System Prompt Template**:
```markdown
You are a workflow generator for Cortex Flow, a multi-agent AI system.

Given a natural language description, generate a valid workflow JSON.

## Available Agents
- **researcher**: Web search, information gathering, data collection
- **analyst**: Data analysis, insight extraction, pattern recognition
- **writer**: Content creation, report generation, formatting

## Available MCP Tools
{mcp_tools_list}

## Workflow Schema
{
  "name": "workflow_name",
  "version": "1.0",
  "description": "Clear description",
  "nodes": [
    {
      "id": "unique_id",
      "agent": "researcher|analyst|writer",
      "instruction": "Detailed task description",
      "depends_on": ["previous_node_id"],
      "timeout": 300
    }
  ],
  "conditional_edges": [
    {
      "source": "node_id",
      "condition": "sentiment == 'positive'",
      "target": "positive_handler",
      "else_target": "negative_handler"
    }
  ],
  "parameters": {}
}

## Rules
1. Use clear, descriptive node IDs (e.g., "research_company", "analyze_data")
2. Instructions must be specific and actionable
3. Ensure proper dependencies (depends_on)
4. Use conditional edges for branching logic
5. Output ONLY valid JSON, no explanation

## Example Input
"Create a workflow that researches a company, analyzes their financial data from the database, and generates a competitive analysis report"

## Example Output
{
  "name": "competitive_analysis",
  "version": "1.0",
  "description": "Research company and generate competitive analysis",
  "nodes": [
    {
      "id": "research_company",
      "agent": "researcher",
      "instruction": "Research comprehensive information about: {company_name}",
      "depends_on": [],
      "timeout": 300
    },
    {
      "id": "query_financials",
      "agent": "researcher",
      "instruction": "Query financial data for {company_name} from database using MCP query_database tool",
      "depends_on": [],
      "timeout": 180
    },
    {
      "id": "analyze_data",
      "agent": "analyst",
      "instruction": "Analyze research findings and financial data:\\n\\nResearch: {research_company}\\nFinancials: {query_financials}",
      "depends_on": ["research_company", "query_financials"],
      "timeout": 240
    },
    {
      "id": "write_report",
      "agent": "writer",
      "instruction": "Create a professional competitive analysis report based on:\\n\\n{analyze_data}",
      "depends_on": ["analyze_data"],
      "timeout": 300,
      "template": "competitive_report"
    }
  ],
  "parameters": {
    "company_name": "Example Corp"
  }
}

Now generate a workflow for: {user_description}
```

**API Implementation**:
```python
# servers/editor_server.py

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/api/workflows/generate", tags=["ai"])
async def generate_workflow(request: WorkflowGenerationRequest):
    """Generate workflow from natural language description."""

    # Get available agents and MCP tools for context
    project_dir = get_project_dir(request.project)
    agents_config = read_json_file(project_dir / "agents.json")
    mcp_config = read_json_file(project_dir / "mcp.json")

    # Build context
    available_agents = list(agents_config.get("agents", {}).keys())
    available_mcp = list(mcp_config.get("servers", {}).keys())

    # Load system prompt template
    system_prompt = load_generation_system_prompt(
        mcp_tools=available_mcp
    )

    # Call OpenAI API
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.description}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        workflow_json = response.choices[0].message.content
        workflow = json.loads(workflow_json)

        # Validate workflow
        try:
            WorkflowTemplate(**workflow)
        except ValidationError as e:
            logger.error(f"Generated invalid workflow: {e}")
            raise HTTPException(
                status_code=500,
                detail="Generated workflow failed validation"
            )

        return {
            "workflow": workflow,
            "confidence": 0.95,
            "suggestions": [
                "Review node instructions for clarity",
                "Adjust timeout values if needed",
                "Test workflow with sample data"
            ]
        }

    except Exception as e:
        logger.error(f"AI generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate workflow: {str(e)}"
        )
```

### 3. Prompt Management

**Directory Structure**:
```
projects/{name}/prompts/
├── system.txt              # System prompt (supervisor)
├── agents/
│   ├── researcher.txt      # Researcher agent prompt
│   ├── analyst.txt         # Analyst agent prompt
│   └── writer.txt          # Writer agent prompt
└── mcp/
    ├── corporate_db.md     # Corporate DB MCP prompt
    └── tavily.md           # Tavily MCP prompt
```

**API Implementation**:
```python
@app.get("/api/projects/{project_name}/prompts", tags=["prompts"])
async def list_prompts(project_name: str):
    """List all prompts in project."""
    project_dir = get_project_dir(project_name)
    prompts_dir = project_dir / "prompts"

    result = {
        "system": None,
        "agents": {},
        "mcp": {}
    }

    # System prompt
    system_file = prompts_dir / "system.txt"
    if system_file.exists():
        result["system"] = system_file.read_text()

    # Agent prompts
    agents_dir = prompts_dir / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.txt"):
            agent_name = agent_file.stem
            result["agents"][agent_name] = agent_file.read_text()

    # MCP prompts
    mcp_dir = prompts_dir / "mcp"
    if mcp_dir.exists():
        for mcp_file in mcp_dir.glob("*.md"):
            server_name = mcp_file.stem
            result["mcp"][server_name] = mcp_file.read_text()

    return result


@app.put("/api/projects/{project_name}/prompts/system", tags=["prompts"])
async def update_system_prompt(project_name: str, data: PromptData):
    """Update system prompt."""
    project_dir = get_project_dir(project_name)
    prompts_dir = project_dir / "prompts"
    prompts_dir.mkdir(exist_ok=True)

    system_file = prompts_dir / "system.txt"
    system_file.write_text(data.content)

    logger.info(f"Updated system prompt for project: {project_name}")

    return {"status": "success", "message": "System prompt updated"}


@app.put("/api/projects/{project_name}/prompts/agents/{agent}", tags=["prompts"])
async def update_agent_prompt(project_name: str, agent: str, data: PromptData):
    """Update agent prompt."""
    project_dir = get_project_dir(project_name)
    agents_dir = project_dir / "prompts" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    agent_file = agents_dir / f"{agent}.txt"
    agent_file.write_text(data.content)

    logger.info(f"Updated {agent} prompt for project: {project_name}")

    return {"status": "success", "message": f"{agent} prompt updated"}
```

**Frontend Component**:
```typescript
export function PromptLibrary() {
  const { data: prompts } = usePrompts();
  const [selectedType, setSelectedType] = useState<'system' | 'agent' | 'mcp'>('system');
  const [selectedIdentifier, setSelectedIdentifier] = useState<string>();

  return (
    <div className="flex h-screen">
      {/* Sidebar: Prompt list */}
      <div className="w-64 border-r">
        <Tabs value={selectedType} onValueChange={setSelectedType}>
          <TabsList>
            <TabsTrigger value="system">System</TabsTrigger>
            <TabsTrigger value="agent">Agents</TabsTrigger>
            <TabsTrigger value="mcp">MCP</TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="p-4">
          {selectedType === 'system' && (
            <Button onClick={() => setSelectedIdentifier('system')}>
              Edit System Prompt
            </Button>
          )}

          {selectedType === 'agent' && (
            <div className="space-y-2">
              {Object.keys(prompts?.agents || {}).map(agent => (
                <Button
                  key={agent}
                  variant="ghost"
                  onClick={() => setSelectedIdentifier(agent)}
                >
                  {agent}
                </Button>
              ))}
            </div>
          )}

          {selectedType === 'mcp' && (
            <div className="space-y-2">
              {Object.keys(prompts?.mcp || {}).map(server => (
                <Button
                  key={server}
                  variant="ghost"
                  onClick={() => setSelectedIdentifier(server)}
                >
                  {server}
                </Button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main: Prompt editor */}
      <div className="flex-1">
        {selectedIdentifier ? (
          <PromptEditor
            type={selectedType}
            identifier={selectedIdentifier}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p>Select a prompt to edit</p>
          </div>
        )}
      </div>
    </div>
  );
}
```

### 4. MCP Integration

**MCP Registry Integration**:
```python
import httpx

MCP_REGISTRY_URL = "https://registry.modelcontextprotocol.io"

@app.get("/api/mcp/registry", tags=["mcp"])
async def browse_mcp_registry(
    search: Optional[str] = None,
    category: Optional[str] = None
):
    """Browse MCP Registry."""

    async with httpx.AsyncClient() as client:
        params = {}
        if search:
            params["search"] = search
        if category:
            params["category"] = category

        response = await client.get(
            f"{MCP_REGISTRY_URL}/servers",
            params=params,
            timeout=30.0
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail="Failed to fetch from MCP Registry"
            )

        return response.json()


@app.get("/api/mcp/registry/{server_id}", tags=["mcp"])
async def get_mcp_server_details(server_id: str):
    """Get MCP server details from registry."""

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MCP_REGISTRY_URL}/servers/{server_id}",
            timeout=30.0
        )

        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Server not found in registry"
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail="Failed to fetch server details"
            )

        return response.json()
```

**Frontend MCP Browser**:
```typescript
export function MCPBrowser() {
  const [search, setSearch] = useState('');
  const { data: servers, isLoading } = useMCPRegistry(search);
  const { mutateAsync: addToProject } = useAddMCPServer();

  const handleAddServer = async (server: MCPServer) => {
    await addToProject({
      server_id: server.id,
      config: {
        type: server.type,
        url: server.url,
        enabled: true,
      }
    });
  };

  return (
    <div className="p-6">
      <div className="mb-4">
        <Input
          placeholder="Search MCP servers..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {servers?.map(server => (
          <Card key={server.id}>
            <CardHeader>
              <CardTitle>{server.name}</CardTitle>
              <CardDescription>{server.description}</CardDescription>
            </CardHeader>

            <CardContent>
              <div className="space-y-2">
                <Badge>{server.category}</Badge>
                <p className="text-sm">
                  Tools: {server.tools?.length || 0}
                </p>
              </div>
            </CardContent>

            <CardFooter>
              <Button onClick={() => handleAddServer(server)}>
                Add to Project
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

---

## Development Phases

### Phase 1: Backend API Base (Week 1) ✅

**Completed**:
- [x] FastAPI server setup
- [x] Projects CRUD endpoints
- [x] Agents/ReAct config endpoints
- [x] JSON file I/O
- [x] Pydantic validation

**Remaining**:
- [ ] Prompts API endpoints
- [ ] Workflows API endpoints
- [ ] MCP API endpoints
- [ ] AI generation endpoint

### Phase 2: Frontend Base (Week 2)

**Tasks**:
1. Initialize Vite + React + TypeScript
   ```bash
   npm create vite@latest web-editor -- --template react-ts
   cd web-editor
   npm install
   ```

2. Install dependencies
   ```bash
   npm install react-router-dom zustand @tanstack/react-query
   npm install reactflow @monaco-editor/react
   npm install axios
   npm install -D tailwindcss postcss autoprefixer
   npm install -D @shadcn/ui
   ```

3. Setup Tailwind CSS
   ```bash
   npx tailwindcss init -p
   ```

4. Configure routing
   ```typescript
   // App.tsx
   import { BrowserRouter, Routes, Route } from 'react-router-dom';

   function App() {
     return (
       <BrowserRouter>
         <Routes>
           <Route path="/" element={<HomePage />} />
           <Route path="/projects" element={<ProjectsPage />} />
           <Route path="/workflows/:id" element={<WorkflowEditorPage />} />
           <Route path="/prompts" element={<PromptsPage />} />
           <Route path="/mcp" element={<MCPPage />} />
         </Routes>
       </BrowserRouter>
     );
   }
   ```

5. Create base layout
6. Implement project list/create
7. Connect to API

### Phase 3: Prompt Management (Week 3)

**Tasks**:
1. Implement prompts API (backend)
2. Create PromptEditor component
3. Create PromptLibrary component
4. Add Monaco editor integration
5. Implement save/load functionality
6. Add template variables support

### Phase 4: Workflow Code Editor (Week 4)

**Tasks**:
1. Implement workflows API (backend)
2. Create WorkflowList component
3. Add Monaco editor for JSON
4. Implement JSON schema validation
5. Add autocomplete support
6. Create workflow save/load
7. Add validation error display

### Phase 5: AI Workflow Generation (Week 5)

**Tasks**:
1. Implement AI generation API (backend)
2. Create system prompt template
3. Add OpenAI integration
4. Create AIAssistant component
5. Implement generation UI
6. Add workflow preview
7. Add edit/save flow

### Phase 6: Workflow Visual Editor (Weeks 6-7)

**Tasks**:
1. Setup React Flow
2. Create custom node types (agent, MCP, conditional)
3. Implement node palette
4. Add drag & drop functionality
5. Create node configuration sidebar
6. Implement JSON ↔ Visual conversion
7. Add edge creation (dependencies)
8. Implement conditional edges
9. Add auto-layout algorithm
10. Create preview/export functionality

### Phase 7: MCP Integration (Week 8)

**Tasks**:
1. Implement MCP registry API (backend)
2. Create MCPBrowser component
3. Add server search/filter
4. Implement server configuration form
5. Add connection testing
6. Create common library management
7. Integrate with workflow editor

### Phase 8: Testing & Execution (Week 9)

**Tasks**:
1. Implement test/preview API (backend)
2. Create TestPanel component
3. Add dry-run execution
4. Implement ExecutionLogs viewer
5. Create ResultViewer component
6. Add real-time log streaming
7. Implement error handling/display

### Phase 9: Polish & Documentation (Week 10)

**Tasks**:
1. UI/UX improvements
2. Add loading states
3. Improve error messages
4. Create user guide
5. Create developer documentation
6. Record video tutorials
7. Write API documentation
8. Add inline help/tooltips

---

## Testing Strategy

### Backend Testing

```python
# tests/test_editor_api.py
import pytest
from fastapi.testclient import TestClient
from servers.editor_server import app

client = TestClient(app)

def test_list_projects():
    """Test GET /api/projects"""
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_project():
    """Test POST /api/projects"""
    data = {
        "name": "test_project",
        "description": "Test project"
    }

    response = client.post("/api/projects", json=data)
    assert response.status_code == 201
    assert response.json()["name"] == "test_project"

def test_update_agents_config():
    """Test PUT /api/projects/{name}/agents"""
    config = {
        "config": {
            "agents": {
                "researcher": {
                    "enabled": True,
                    "model": "gpt-4"
                }
            }
        }
    }

    response = client.put("/api/projects/default/agents", json=config)
    assert response.status_code == 200
```

### Frontend Testing

```typescript
// tests/ProjectList.test.tsx
import { render, screen } from '@testing-library/react';
import { ProjectList } from '@/components/projects/ProjectList';

describe('ProjectList', () => {
  it('renders projects', async () => {
    render(<ProjectList onProjectSelect={jest.fn()} />);

    expect(await screen.findByText('default')).toBeInTheDocument();
  });

  it('calls onProjectSelect when clicking project', async () => {
    const onSelect = jest.fn();
    render(<ProjectList onProjectSelect={onSelect} />);

    const project = await screen.findByText('default');
    project.click();

    expect(onSelect).toHaveBeenCalled();
  });
});
```

### E2E Testing (Playwright)

```typescript
// tests/e2e/workflow-creation.spec.ts
import { test, expect } from '@playwright/test';

test('create workflow visually', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Navigate to workflows
  await page.click('text=Workflows');
  await page.click('text=New Workflow');

  // Switch to visual editor
  await page.click('text=Visual');

  // Drag researcher node
  await page.dragAndDrop(
    '[data-node-type="researcher"]',
    '.react-flow-renderer',
    { targetPosition: { x: 100, y: 100 } }
  );

  // Configure node
  await page.click('[data-node-id="researcher-1"]');
  await page.fill('[name="instruction"]', 'Research AI trends');

  // Save workflow
  await page.click('text=Save');

  // Verify saved
  await expect(page.locator('text=Workflow saved')).toBeVisible();
});
```

---

## Deployment

### Development

```bash
# Backend
cd cortex-flow
source .venv/bin/activate
python servers/editor_server.py

# Frontend
cd web-editor
npm run dev
```

### Production

**Backend (Docker)**:
```dockerfile
# Dockerfile.editor
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY servers/editor_server.py servers/
COPY projects/ projects/

EXPOSE 8002

CMD ["python", "servers/editor_server.py"]
```

**Frontend (Static Build)**:
```bash
cd web-editor
npm run build

# Deploy dist/ to:
# - Netlify
# - Vercel
# - S3 + CloudFront
# - Nginx
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  editor-api:
    build:
      context: .
      dockerfile: Dockerfile.editor
    ports:
      - "8002:8002"
    volumes:
      - ./projects:/app/projects
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  editor-web:
    image: nginx:alpine
    ports:
      - "3000:80"
    volumes:
      - ./web-editor/dist:/usr/share/nginx/html
```

---

## Next Steps

**Immediate** (This session):
1. ✅ Complete backend Phase 1
2. Add remaining backend endpoints (Prompts, Workflows, MCP)
3. Create basic frontend skeleton

**Short-term** (Next sessions):
1. Implement Phase 2: Frontend base
2. Implement Phase 3: Prompt management
3. Implement Phase 4: Code editor

**Long-term** (Weeks 2-10):
1. Complete all phases per schedule
2. Iterative testing and refinement
3. Documentation and tutorials
4. Production deployment

---

**Last Updated**: 2025-10-07
**Status**: Backend Phase 1 Complete ✅
**Next Phase**: Backend Endpoints Completion
