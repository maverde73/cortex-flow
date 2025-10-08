# Cortex Flow Web Application

The Cortex Flow Web Application is a powerful, modern interface for building, managing, and testing AI workflows. Built with React, TypeScript, and TailwindCSS, it provides an intuitive visual environment for orchestrating multi-agent AI systems.

## 📋 Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [User Interface](#user-interface)
- [Core Components](#core-components)
- [Documentation](#documentation)

## 🌟 Features

### Visual Workflow Editor
- **Drag-and-drop interface** for building complex workflows
- **Real-time validation** with instant feedback
- **Natural language conversion** - describe workflows in plain English
- **Visual flow diagram** with automatic layout
- **Import/Export** workflows as JSON templates

### Process Management
- **Real-time monitoring** of all agent processes
- **One-click controls** to start/stop individual agents
- **Resource tracking** - CPU and memory usage per agent
- **Log viewing** for debugging and monitoring
- **Auto-discovery** of running processes

### Testing & Debugging
- **Agent Playground** - Test individual agents interactively
- **Workflow Debugger** - Step-by-step execution tracing
- **Execution history** with detailed logs
- **Performance metrics** for optimization

### Project Management
- **Multi-project support** with isolated configurations
- **Project templates** for quick setup
- **Configuration management** per project
- **Import/Export** project settings

### MCP Integration
- **Visual MCP server configuration**
- **Tool discovery and testing**
- **Prompt management** for servers
- **Real-time connection status**

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python backend server running (see main README)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Build the application**
```bash
npm run build
```

4. **Start the backend server**
```bash
cd ..
python servers/editor_server.py
```

5. **Access the application**
Open http://localhost:8002 in your browser

### Development Mode

For development with hot-reload:
```bash
cd frontend
npm run dev
```

## 🖥️ User Interface

### Dashboard
The main landing page showing:
- System status overview
- Active agents and their states
- Recent projects and workflows
- Quick action buttons

### Sidebar Navigation
- **Dashboard** - System overview
- **Projects** - Project management
- **Workflows** - Workflow editor and templates
- **Agents** - Agent configuration
- **Testing** - Test playground and debugger
- **Prompts** - Prompt management
- **MCP** - MCP server configuration
- **LLM** - Model configuration

### Status Bar
Bottom bar showing:
- **Agent badges** - Click to start/stop agents
- **Running count** - Active/Total agents
- **Global controls** - Start All, Stop All, Refresh

## 🔧 Core Components

### Workflow Editor
Located in `src/pages/WorkflowsPage.tsx`
- Visual workflow designer
- Node-based editing
- Condition configuration
- Parameter management

### Process Manager
Located in `src/components/ProcessStatusBar.tsx`
- Real-time process monitoring
- Start/stop controls
- Resource usage display

### Testing Tools
Located in `src/pages/TestingPage.tsx`
- Agent playground for individual testing
- Workflow debugger for full execution
- Step-by-step tracing

### Project Selector
Located in `src/components/Layout.tsx`
- Quick project switching
- Active project indicator
- Project activation control

## 📚 Documentation

- [User Guide](./user-guide.md) - Detailed usage instructions
- [Architecture](./architecture.md) - Technical architecture details
- [API Reference](./api-reference.md) - Backend API documentation
- [Process Management](./process-management.md) - Agent process control
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions

## 🎨 Technology Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type-safe development
- **TailwindCSS** - Utility-first styling
- **React Query** - Server state management
- **React Router** - Client-side routing
- **Zustand** - Client state management
- **React Flow** - Visual workflow diagrams

### Build Tools
- **Vite** - Fast build tool
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **TypeScript Compiler** - Type checking

## 🔄 State Management

### Server State (React Query)
- API data fetching and caching
- Automatic refetching
- Optimistic updates
- Background synchronization

### Client State (Zustand)
- UI state (sidebar, modals)
- Current project selection
- Editor state
- User preferences

## 🎯 Key Pages

### Dashboard (`/`)
System overview and quick access

### Projects (`/projects`)
Create, manage, and configure projects

### Workflows (`/workflows`)
Visual workflow editor and management

### Agents (`/agents`)
Agent configuration and status

### Testing (`/testing`)
Interactive testing playground

### Prompts (`/prompts`)
Prompt template management

### MCP (`/mcp`)
MCP server configuration

### LLM (`/llm`)
Language model settings

## 🛠️ Development

### File Structure
```
frontend/
├── src/
│   ├── components/     # Reusable components
│   │   ├── Layout.tsx
│   │   ├── ProcessStatusBar.tsx
│   │   └── ...
│   ├── pages/          # Page components
│   │   ├── Dashboard.tsx
│   │   ├── WorkflowsPage.tsx
│   │   └── ...
│   ├── services/       # API services
│   │   └── api.ts
│   ├── store/          # State management
│   │   └── useStore.ts
│   ├── types/          # TypeScript types
│   │   └── api.ts
│   ├── App.tsx         # Main app component
│   └── main.tsx        # Entry point
├── public/             # Static assets
├── index.html          # HTML template
├── package.json        # Dependencies
├── tsconfig.json       # TypeScript config
├── vite.config.ts      # Vite config
└── tailwind.config.js  # Tailwind config
```

### Adding New Features

1. **Create component** in `src/components/`
2. **Add page** if needed in `src/pages/`
3. **Update API types** in `src/types/api.ts`
4. **Add API methods** in `src/services/api.ts`
5. **Update routing** in `src/App.tsx`

## 🔐 Security

- API requests use secure HTTP headers
- Input validation on all forms
- XSS protection via React
- CORS configured on backend

## 🚦 Performance

- Code splitting for faster loads
- Lazy loading of routes
- Optimized bundle size
- Efficient re-renders with React Query
- Virtual scrolling for large lists

## 🐛 Debugging

### Browser DevTools
- React DevTools for component inspection
- Network tab for API monitoring
- Console for error messages

### Backend Logs
- Check `logs/` directory for agent logs
- Editor server logs in console
- Process manager logs for debugging

## 🤝 Contributing

See main [Contributing Guide](../../CONTRIBUTING.md) for guidelines.

## 📝 License

Part of the Cortex Flow project - see main [LICENSE](../../LICENSE) file.

---

**Next Steps**: Check out the [User Guide](./user-guide.md) for detailed usage instructions!