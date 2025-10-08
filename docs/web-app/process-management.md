# Process Management System

The Cortex Flow process management system provides comprehensive control over AI agent processes, enabling users to start, stop, monitor, and debug agents through both the web interface and API.

## Overview

The process management system consists of:
- **Backend ProcessManager**: Python-based process lifecycle management
- **REST API**: FastAPI endpoints for process control
- **Frontend Status Bar**: Real-time visual process monitoring
- **Auto-Discovery**: Automatic detection of running processes

## Architecture

### Backend Components

```python
# utils/process_manager.py
class ProcessManager:
    """Manages agent and workflow processes."""

    AGENTS_CONFIG = {
        "researcher": {"port": 8001, "script": "servers/researcher_server.py"},
        "analyst": {"port": 8003, "script": "servers/analyst_server.py"},
        "writer": {"port": 8004, "script": "servers/writer_server.py"},
        "supervisor": {"port": 8000, "script": "servers/supervisor_server.py"},
    }
```

### Process Lifecycle

```
   ┌─────────┐
   │ Stopped │
   └────┬────┘
        │ start_agent()
        ▼
   ┌──────────┐
   │ Starting │ ──── Creates PID file
   └────┬─────┘      Sets PYTHONPATH
        │            Launches subprocess
        ▼
   ┌─────────┐
   │ Running │ ──── Monitors via psutil
   └────┬────┘      Tracks resources
        │ stop_agent()
        ▼
   ┌──────────┐
   │ Stopping │ ──── Graceful termination
   └────┬─────┘      Cleanup PID file
        │
        ▼
   ┌─────────┐
   │ Stopped │
   └─────────┘
```

## Features

### Auto-Discovery

The system automatically discovers running processes through multiple methods:

1. **PID File Check**: Looks for existing PID files in `logs/` directory
2. **Port Scanning**: Checks if configured ports are in use
3. **Process Name Matching**: Searches for processes by script name

```python
def get_agent_status(self, agent_name: str) -> ProcessInfo:
    # 1. Check PID file
    pid = self._read_pid(agent_name)
    if pid and self._is_process_running(pid):
        return ProcessInfo(...)

    # 2. Check by port
    port_pid = self._find_process_by_port(config["port"])
    if port_pid:
        self._write_pid(agent_name, port_pid)  # Create PID file
        return ProcessInfo(...)

    # 3. Check by script name
    script_pid = self._find_process_by_script(config["script"])
    if script_pid:
        self._write_pid(agent_name, script_pid)
        return ProcessInfo(...)
```

### Resource Monitoring

Real-time tracking of process resources:

- **CPU Usage**: Percentage of CPU utilized
- **Memory Usage**: RAM consumption in MB
- **Uptime**: Time since process started
- **Port Status**: Network port binding status

### Process Control

#### Starting Processes

```python
def start_agent(self, agent_name: str) -> ProcessInfo:
    # Set environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(self.project_root)  # Critical for imports

    # Launch process
    with open(log_file, 'a') as log:
        process = subprocess.Popen(
            ["python", str(script_path)],
            cwd=str(self.project_root),
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True  # Detach from parent
        )
```

#### Stopping Processes

Graceful shutdown with fallback to force kill:

```python
def stop_agent(self, agent_name: str) -> ProcessInfo:
    process = psutil.Process(pid)

    # Try graceful shutdown
    process.terminate()
    try:
        process.wait(timeout=5)
    except psutil.TimeoutExpired:
        # Force kill if needed
        process.kill()
        process.wait(timeout=5)
```

## Web Interface

### Process Status Bar

Located at the bottom of the application, the status bar provides:

![Process Status Bar](./images/process-status-bar.png)

#### Visual Indicators

- **🟢 Green Badge**: Agent is running
- **⚪ Gray Badge**: Agent is stopped
- **🟡 Yellow Badge**: Agent is starting
- **🔴 Red Badge**: Agent has error

#### Interactive Controls

**Single Agent Control:**
- Click any agent badge to toggle its state
- Hover for details (uptime, port, status)

**Batch Operations:**
- **▶️ Start All**: Launch all configured agents
- **⏹️ Stop All**: Stop all running agents
- **🔄 Refresh**: Update status immediately

### React Component

```typescript
// components/ProcessStatusBar.tsx
function ProcessBadge({ process, onToggle }: ProcessBadgeProps) {
  const statusColor = {
    running: 'bg-green-500',
    stopped: 'bg-gray-400',
    starting: 'bg-yellow-500',
    error: 'bg-red-500',
  }[process.status];

  return (
    <button
      onClick={onToggle}
      className={`px-3 py-1 rounded-full ${statusColor}`}
      title={`Click to ${process.status === 'running' ? 'stop' : 'start'}`}
    >
      {statusIcon} {process.name}
      {process.status === 'running' && ` (${formatUptime()})`}
    </button>
  );
}
```

## API Endpoints

### Get Process Status
```http
GET /api/processes/status
```

Returns status of all configured processes.

### Start Process
```http
POST /api/processes/start
Body: { "name": "researcher" }
```

Starts a specific agent process.

### Stop Process
```http
POST /api/processes/stop
Body: { "name": "researcher" }
```

Stops a specific agent process.

### Start All Processes
```http
POST /api/processes/start-all
```

Starts all configured agents.

### Stop All Processes
```http
POST /api/processes/stop-all
```

Stops all running agents.

### Get Process Logs
```http
GET /api/processes/{name}/logs?lines=100
```

Returns the last N lines of process logs.

## Configuration

### Agent Configuration

Agents are configured in `utils/process_manager.py`:

```python
AGENTS_CONFIG = {
    "agent_name": {
        "port": 8000,           # Network port
        "script": "path/to/server.py"  # Script to execute
    }
}
```

### Adding New Agents

1. **Create the agent server** in `servers/`:
```python
# servers/new_agent_server.py
from fastapi import FastAPI

app = FastAPI()

@app.post("/invoke")
async def invoke(request: dict):
    # Agent logic here
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
```

2. **Add to configuration**:
```python
AGENTS_CONFIG = {
    # ... existing agents
    "new_agent": {
        "port": 8005,
        "script": "servers/new_agent_server.py"
    }
}
```

3. **Restart the editor server** to apply changes

## Logging

### Log Files

All process output is captured in log files:

```
logs/
├── researcher.log    # Researcher agent logs
├── analyst.log       # Analyst agent logs
├── writer.log        # Writer agent logs
├── supervisor.log    # Supervisor agent logs
├── researcher.pid    # PID files for tracking
├── analyst.pid
└── ...
```

### Viewing Logs

**Via API:**
```bash
curl http://localhost:8002/api/processes/researcher/logs?lines=50
```

**Via File System:**
```bash
tail -f logs/researcher.log
```

**Via Web UI:**
- Click on agent badge → View Logs (if available)

## Troubleshooting

### Common Issues

#### Agent Won't Start

**Symptoms:**
- Badge stays gray after clicking
- Briefly turns green then gray

**Causes and Solutions:**

1. **Port Already in Use**
```bash
# Check what's using the port
lsof -i :8001

# Kill the process if needed
kill -9 <PID>
```

2. **Python Import Errors**
- Check PYTHONPATH is set correctly
- Verify dependencies installed: `pip install -r requirements.txt`
- Check logs for import errors

3. **Permission Issues**
```bash
# Ensure scripts are executable
chmod +x servers/*.py

# Check file ownership
ls -la servers/
```

#### Agent Crashes Immediately

**Check the logs:**
```bash
tail -n 50 logs/agent_name.log
```

**Common causes:**
- Missing environment variables (API keys)
- Configuration errors
- Database connection issues

#### Cannot Stop Agent

**Force stop via command line:**
```bash
# Find the process
ps aux | grep researcher_server

# Force kill
kill -9 <PID>

# Remove stale PID file
rm logs/researcher.pid
```

### Status Bar Not Updating

**Auto-refresh is set to 5 seconds. To force refresh:**
- Click the 🔄 Refresh button
- Reload the page (F5)
- Check browser console for errors

### Debugging Process Issues

**Enable debug logging:**

```python
# In process_manager.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Monitor system resources:**
```bash
# Watch CPU and memory
htop

# Monitor network connections
netstat -tulpn | grep python
```

## Performance Considerations

### Resource Usage

Each agent typically uses:
- **CPU**: 1-5% idle, 10-50% active
- **Memory**: 100-300 MB
- **Port**: One dedicated network port

### Optimization Tips

1. **Start only needed agents**: Don't run all agents if not required
2. **Monitor resource usage**: Use the status bar metrics
3. **Rotate logs**: Prevent disk space issues
```bash
# Add to crontab
0 0 * * * find /path/to/logs -name "*.log" -mtime +7 -delete
```

4. **Use process limits**: Set resource constraints
```python
# In start_agent
import resource
resource.setrlimit(resource.RLIMIT_AS, (500 * 1024 * 1024, -1))  # 500MB limit
```

## Security

### Best Practices

1. **Run with minimum privileges**: Don't run as root
2. **Secure API endpoints**: Add authentication in production
3. **Validate input**: Sanitize process names
4. **Monitor logs**: Watch for suspicious activity
5. **Network isolation**: Use firewall rules for agent ports

### Production Deployment

For production environments:

1. **Use a process supervisor** like systemd:
```ini
# /etc/systemd/system/cortex-researcher.service
[Unit]
Description=Cortex Researcher Agent
After=network.target

[Service]
Type=simple
User=cortex
WorkingDirectory=/opt/cortex-flow
Environment="PYTHONPATH=/opt/cortex-flow"
ExecStart=/usr/bin/python3 /opt/cortex-flow/servers/researcher_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

2. **Implement health checks**:
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}
```

3. **Use environment-specific configs**:
```python
# config.py
class Settings:
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        if self.environment == "production":
            self.log_level = "INFO"
            self.debug = False
        else:
            self.log_level = "DEBUG"
            self.debug = True
```

## Integration with Workflows

Workflows automatically use the process management system:

1. **Pre-execution checks**: Verify required agents are running
2. **Auto-start**: Optionally start missing agents
3. **Health monitoring**: Check agent health during execution
4. **Graceful degradation**: Handle agent failures

```python
# In workflow execution
async def execute_workflow(workflow_id: str):
    # Check required agents
    required_agents = extract_required_agents(workflow)

    for agent in required_agents:
        status = process_manager.get_agent_status(agent)
        if status.status != "running":
            # Auto-start or fail
            if auto_start_enabled:
                process_manager.start_agent(agent)
            else:
                raise AgentNotRunningError(f"{agent} is not running")
```

## Future Enhancements

Planned improvements:

1. **WebSocket support**: Real-time status updates
2. **Process groups**: Start/stop related agents together
3. **Resource limits**: CPU/memory constraints per agent
4. **Scheduling**: Cron-like agent scheduling
5. **Clustering**: Multi-node agent deployment
6. **Metrics dashboard**: Prometheus/Grafana integration
7. **Log streaming**: Real-time log viewing in UI
8. **Auto-scaling**: Dynamic agent spawning based on load

---

For more information, see the [API Reference](./api-reference.md) for detailed endpoint documentation.