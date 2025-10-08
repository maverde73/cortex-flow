# Cortex Flow Web Application - User Guide

This comprehensive guide will help you master the Cortex Flow web application, from basic tasks to advanced workflow creation.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Managing Projects](#managing-projects)
4. [Building Workflows](#building-workflows)
5. [Agent Management](#agent-management)
6. [Testing & Debugging](#testing--debugging)
7. [Prompt Management](#prompt-management)
8. [MCP Configuration](#mcp-configuration)
9. [LLM Settings](#llm-settings)
10. [Tips & Best Practices](#tips--best-practices)

## Getting Started

### First-Time Setup

1. **Access the Application**
   - Open your browser and navigate to http://localhost:8002
   - You'll see the dashboard with the sidebar navigation

2. **Create Your First Project**
   - Click on "Projects" in the sidebar
   - Click "Create New Project"
   - Enter a name and description
   - Click "Create"

3. **Start the Agents**
   - Look at the bottom status bar
   - Click "Start All" to start all agents
   - Or click individual agent badges to start specific agents
   - Green badges = running, Gray badges = stopped

## Dashboard Overview

The dashboard provides a quick overview of your system:

### Key Elements

- **System Status**: Shows overall health and active agents
- **Recent Projects**: Quick access to your most recent work
- **Active Workflows**: Currently running or recent workflows
- **Quick Actions**: Common tasks you can perform immediately

### Navigation

The sidebar contains all major sections:
- **📊 Dashboard** - System overview (current page)
- **📁 Projects** - Manage your projects
- **🔄 Workflows** - Create and edit workflows
- **🤖 Agents** - Configure agent settings
- **🧪 Testing** - Test agents and workflows
- **💬 Prompts** - Manage prompt templates
- **🔌 MCP** - Configure MCP servers
- **🧠 LLM** - Language model settings

## Managing Projects

Projects organize your workflows, prompts, and configurations.

### Creating a Project

1. Navigate to **Projects** page
2. Click **"New Project"** button
3. Fill in the form:
   - **Name**: Unique identifier (no spaces)
   - **Description**: Brief description of purpose
   - **Configuration**: Optional JSON configuration
4. Click **"Create"**

### Switching Projects

Use the project selector in the sidebar:
1. Click on the current project name (bottom of sidebar)
2. Select a different project from the dropdown
3. The app will switch context to that project

### Project Settings

Each project can have:
- **Custom Prompts**: Project-specific prompt templates
- **Workflows**: Workflows belong to the active project
- **Configuration**: Environment variables and settings

## Building Workflows

The workflow editor is the heart of Cortex Flow.

### Visual Editor

1. **Navigate to Workflows**
2. **Create New Workflow**
   - Click "New Workflow"
   - Choose creation method:
     - **Visual Editor**: Drag-and-drop interface
     - **Natural Language**: Describe in plain English
     - **Import JSON**: Upload existing workflow

### Workflow Components

#### Nodes
Each node represents an action:
- **Agent Nodes**: Invoke specific agents
- **Tool Nodes**: Execute tools directly
- **Decision Nodes**: Conditional branching
- **Input/Output Nodes**: Data flow control

#### Connections
Draw connections between nodes:
1. Click on a node's output port
2. Drag to another node's input port
3. Release to create connection

#### Node Configuration
Double-click any node to configure:
- **Name**: Display name
- **Agent/Tool**: Which agent or tool to use
- **Parameters**: Input parameters
- **Conditions**: When to execute (for conditional nodes)

### Natural Language Mode

1. Click **"Describe in Natural Language"**
2. Type your workflow description:
   ```
   "First, research the topic using the web.
   Then analyze the findings.
   Finally, write a summary report."
   ```
3. Click **"Generate Workflow"**
4. Review and edit the generated workflow

### Workflow Validation

The editor validates in real-time:
- **Green checkmark**: Valid workflow
- **Yellow warning**: Non-critical issues
- **Red error**: Must be fixed before running

Common validation errors:
- Disconnected nodes
- Missing required parameters
- Circular dependencies
- Invalid agent references

## Agent Management

### Process Control

The **Process Status Bar** (bottom of screen) shows all agents:

#### Starting/Stopping Agents
- **Click any agent badge** to toggle its state
- **Green badge** = Running
- **Gray badge** = Stopped
- **Yellow badge** = Starting
- **Red badge** = Error

#### Batch Operations
- **Start All**: Starts all configured agents
- **Stop All**: Stops all running agents
- **Refresh**: Updates status immediately

### Agent Configuration

Navigate to **Agents** page to configure:

1. **Select an Agent** from the list
2. **Configure Settings**:
   - **Model**: Which LLM to use
   - **Temperature**: Creativity level (0-1)
   - **Max Tokens**: Output length limit
   - **Tools**: Available tools for the agent
   - **System Prompt**: Agent's instructions

3. **Save Configuration**

### Viewing Agent Logs

1. Click on an agent in the status bar
2. Select **"View Logs"** (if available)
3. Logs show:
   - Startup messages
   - Request/response pairs
   - Error messages
   - Performance metrics

## Testing & Debugging

### Agent Playground

Test individual agents interactively:

1. Navigate to **Testing** → **Agent Playground**
2. **Select an Agent** from dropdown
3. **Enter Test Input** in the text area
4. Click **"Execute"**
5. View the response and execution details

#### Execution Details Include:
- **Thinking Process**: Agent's reasoning
- **Actions Taken**: Tools used
- **Observations**: Results from tools
- **Final Output**: Agent's response
- **Execution Time**: Performance metrics

### Workflow Debugger

Debug complete workflows step-by-step:

1. Navigate to **Testing** → **Workflow Debugger**
2. **Select a Workflow** to test
3. **Provide Input Data**
4. Click **"Execute with Debugging"**

#### Debug Features:
- **Step-by-step execution**: Pause at each node
- **State inspection**: View data at each step
- **Breakpoints**: Set stops at specific nodes
- **Variable watching**: Monitor specific values
- **Execution trace**: Complete history

### Common Testing Patterns

#### Test Individual Components First
1. Test each agent in the playground
2. Verify expected outputs
3. Then test the complete workflow

#### Use Test Data Sets
1. Create standard test inputs
2. Save successful outputs as baselines
3. Compare new runs against baselines

## Prompt Management

Manage reusable prompt templates:

### Creating Prompts

1. Navigate to **Prompts** page
2. Click **"New Prompt"**
3. Fill in:
   - **Name**: Unique identifier
   - **Description**: What it's for
   - **Template**: The prompt text with {variables}
   - **Variables**: Define expected inputs

Example:
```
Name: research_prompt
Template: "Research {topic} focusing on {aspects}.
          Provide {num_points} key findings."
Variables: topic, aspects, num_points
```

### Using Prompts in Workflows

1. In workflow editor, add a node
2. Select "Prompt" as the type
3. Choose your prompt template
4. Map workflow variables to prompt variables

## MCP Configuration

Configure Model Context Protocol servers:

### Adding MCP Servers

1. Navigate to **MCP** page
2. Click **"Add Server"**
3. Configure:
   - **Name**: Server identifier
   - **URL**: Server endpoint
   - **Authentication**: API keys if needed
   - **Tools**: Available tools from this server

### Testing MCP Connections

1. Click **"Test Connection"** next to server
2. View response to verify:
   - Connection successful
   - Available tools listed
   - Proper authentication

## LLM Settings

Configure language model providers:

### Supported Providers

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- Groq
- OpenRouter

### Configuration Steps

1. Navigate to **LLM** page
2. Select a provider
3. Enter configuration:
   - **API Key**: Your provider key
   - **Model Selection**: Default model
   - **Request Limits**: Rate limiting
   - **Fallback Options**: Backup models

### Model Selection Strategy

- **Primary Model**: First choice for all requests
- **Fallback Models**: Used if primary fails
- **Cost Optimization**: Route by task complexity

## Tips & Best Practices

### Workflow Design

1. **Start Simple**: Build basic workflows first
2. **Test Incrementally**: Test each addition
3. **Use Templates**: Save successful patterns
4. **Document Purpose**: Add descriptions to nodes

### Performance Optimization

1. **Parallel Execution**: Use parallel nodes when possible
2. **Cache Results**: Enable caching for expensive operations
3. **Limit Iterations**: Set max loops for iterative workflows
4. **Monitor Resources**: Watch CPU/memory in status bar

### Error Handling

1. **Add Error Nodes**: Handle failures gracefully
2. **Set Timeouts**: Prevent infinite waits
3. **Log Everything**: Enable detailed logging for debugging
4. **Test Edge Cases**: Try unusual inputs

### Organization

1. **Naming Conventions**: Use consistent naming
2. **Project Structure**: One project per domain
3. **Version Control**: Export workflows regularly
4. **Documentation**: Document complex workflows

## Keyboard Shortcuts

- **Ctrl/Cmd + S**: Save current workflow
- **Ctrl/Cmd + Z**: Undo last action
- **Ctrl/Cmd + Y**: Redo action
- **Ctrl/Cmd + D**: Duplicate selected node
- **Delete**: Remove selected node/connection
- **Space**: Pan canvas (hold and drag)
- **Ctrl/Cmd + +/-**: Zoom in/out

## Troubleshooting

### Common Issues

#### Agents Won't Start
- Check if ports are already in use
- Verify Python environment is activated
- Check logs in `logs/` directory
- Ensure all dependencies installed

#### Workflow Fails
- Check agent status (all required agents running?)
- Verify input format matches expected schema
- Review error messages in execution trace
- Test individual nodes separately

#### Connection Errors
- Verify backend server is running
- Check network/firewall settings
- Ensure correct API keys configured
- Test with simple ping endpoint

## Getting Help

- **Documentation**: Check `/docs` folder
- **Logs**: Review `logs/` directory
- **API Docs**: Visit http://localhost:8002/docs
- **Community**: File issues on GitHub

---

**Next Steps**: Try creating your first workflow using the [Workflow Editor](#building-workflows)!