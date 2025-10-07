# Cortex Flow Web Editor

Visual IDE for managing multi-agent AI workflows with drag-and-drop interface, code editing, and AI-assisted generation.

---

## 🎯 Quick Start

### Backend (API)

```bash
# Start editor API server
source .venv/bin/activate
python servers/editor_server.py

# Server runs on http://localhost:8002
# API docs: http://localhost:8002/docs
```

### Frontend (Coming Soon)

```bash
cd web-editor
npm install
npm run dev

# UI runs on http://localhost:3000
```

---

## 📚 Documentation

- [**Implementation Guide**](IMPLEMENTATION_GUIDE.md) - Complete technical documentation
- [**API Reference**](API_REFERENCE.md) - REST API endpoints (coming soon)
- [**User Guide**](USER_GUIDE.md) - End-user documentation (coming soon)

---

## 🌟 Features

### ✅ Available Now (Phase 1)

- **Project Management API**
  - List, create, update, delete projects
  - Multi-project support
  - Activate/deactivate projects

- **Agent Configuration API**
  - Configure agent settings
  - ReAct mode parameters
  - LLM provider selection

### 🚧 In Development

- **Prompt Management** (Phase 3)
  - System prompts editor
  - Agent prompts library
  - MCP prompts configuration

- **Workflow Editor** (Phases 4-6)
  - Visual drag & drop interface
  - Code editor with validation
  - AI-assisted generation

- **MCP Integration** (Phase 7)
  - Browse MCP Registry
  - Configure servers
  - Common library

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│      React Frontend (Port 3000)     │
│  ┌──────────┐  ┌──────────┐        │
│  │ Projects │  │ Workflows│        │
│  │  Editor  │  │  Editor  │        │
│  └──────────┘  └──────────┘        │
└────────────────┬────────────────────┘
                 │ REST API
┌────────────────▼────────────────────┐
│    FastAPI Backend (Port 8002)      │
│  ✅ Projects  ⏳ Prompts  ⏳ Workflows │
└────────────────┬────────────────────┘
                 │ File I/O
┌────────────────▼────────────────────┐
│        projects/ Directory          │
│  ├─ default/project.json            │
│  ├─ default/agents.json             │
│  └─ default/workflows/*.json        │
└─────────────────────────────────────┘
```

---

## 🔧 Current API Endpoints

### Projects

```http
GET    /api/projects              # List all
GET    /api/projects/{name}       # Get details
POST   /api/projects              # Create
PUT    /api/projects/{name}       # Update
DELETE /api/projects/{name}       # Delete
POST   /api/projects/{name}/activate  # Activate
```

### Agents & ReAct

```http
GET    /api/projects/{name}/agents  # Get agents config
PUT    /api/projects/{name}/agents  # Update agents config
GET    /api/projects/{name}/react   # Get ReAct config
PUT    /api/projects/{name}/react   # Update ReAct config
```

**OpenAPI Docs**: http://localhost:8002/docs

---

## 📋 Development Status

| Phase | Feature | Status | ETA |
|-------|---------|--------|-----|
| 1 | Backend Base | ✅ Complete | - |
| 1 | Remaining Endpoints | 🚧 In Progress | Week 1 |
| 2 | Frontend Base | ⏳ Pending | Week 2 |
| 3 | Prompt Management | ⏳ Pending | Week 3 |
| 4 | Workflow Code Editor | ⏳ Pending | Week 4 |
| 5 | AI Generation | ⏳ Pending | Week 5 |
| 6 | Visual Editor | ⏳ Pending | Weeks 6-7 |
| 7 | MCP Integration | ⏳ Pending | Week 8 |
| 8 | Testing/Preview | ⏳ Pending | Week 9 |
| 9 | Documentation | ⏳ Pending | Week 10 |

**Total Timeline**: 10 weeks

---

## 🎨 Key Features (Planned)

### Visual Workflow Editor
- Drag & drop node-based interface (React Flow)
- Agent nodes (researcher, analyst, writer)
- MCP tool nodes (database, API, files)
- Conditional routing
- Real-time preview

### AI-Assisted Generation
- Natural language → workflow JSON
- Smart agent selection
- Dependency resolution
- Validation & suggestions

### Prompt Management
- Monaco editor with syntax highlighting
- Template variables
- Version history
- Library of pre-built prompts

### MCP Integration
- Browse official MCP Registry
- One-click server configuration
- Connection testing
- Common library for sharing

---

## 🚀 Technology Stack

**Backend**:
- FastAPI (REST API)
- Pydantic (validation)
- OpenAI API (AI generation)

**Frontend**:
- React 18 + TypeScript
- React Flow (visual editor)
- Monaco Editor (code editor)
- Tailwind CSS + shadcn/ui
- Zustand (state)
- TanStack Query (data fetching)

---

## 📖 Example Usage (API)

### Create a Project

```bash
curl -X POST http://localhost:8002/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_project",
    "description": "My AI workflow project"
  }'
```

### Get Project Details

```bash
curl http://localhost:8002/api/projects/my_project
```

### Update ReAct Config

```bash
curl -X PUT http://localhost:8002/api/projects/my_project/react \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "max_iterations": 30,
      "enable_verbose_logging": true
    }
  }'
```

---

## 🤝 Contributing

1. Read [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for architecture details
2. Pick a phase/feature to implement
3. Follow the coding standards
4. Write tests
5. Submit PR

---

## 📝 License

Same as Cortex Flow main project.

---

**Version**: 1.0.0-alpha
**Status**: 🚧 Early Development
**Last Updated**: 2025-10-07
