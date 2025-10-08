"""
Process Manager

Manages agent and workflow processes lifecycle (start, stop, status monitoring).
"""

import os
import signal
import subprocess
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

ProcessType = Literal["agent", "workflow"]
ProcessStatus = Literal["running", "stopped", "error", "starting"]


class ProcessInfo(BaseModel):
    """Information about a running process."""
    pid: int
    name: str
    type: ProcessType
    status: ProcessStatus
    port: Optional[int] = None
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    uptime_seconds: float = 0.0
    log_file: Optional[str] = None


class ProcessManager:
    """Manages agent and workflow processes."""

    # Agent configurations
    AGENTS_CONFIG = {
        "researcher": {"port": 8001, "script": "servers/researcher_server.py"},
        "analyst": {"port": 8003, "script": "servers/analyst_server.py"},
        "writer": {"port": 8004, "script": "servers/writer_server.py"},
        "supervisor": {"port": 8000, "script": "servers/supervisor_server.py"},
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logs_dir = project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)

    def _get_pid_file(self, name: str) -> Path:
        """Get PID file path for a process."""
        return self.logs_dir / f"{name}.pid"

    def _get_log_file(self, name: str) -> Path:
        """Get log file path for a process."""
        return self.logs_dir / f"{name}.log"

    def _read_pid(self, name: str) -> Optional[int]:
        """Read PID from PID file."""
        pid_file = self._get_pid_file(name)
        if not pid_file.exists():
            return None

        try:
            with open(pid_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return None

    def _write_pid(self, name: str, pid: int):
        """Write PID to PID file."""
        pid_file = self._get_pid_file(name)
        with open(pid_file, 'w') as f:
            f.write(str(pid))

    def _remove_pid(self, name: str):
        """Remove PID file."""
        pid_file = self._get_pid_file(name)
        if pid_file.exists():
            pid_file.unlink()

    def _is_process_running(self, pid: int) -> bool:
        """Check if process is running."""
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def _get_process_stats(self, pid: int) -> Dict[str, float]:
        """Get process CPU and memory stats."""
        try:
            process = psutil.Process(pid)
            return {
                "cpu_percent": process.cpu_percent(interval=0.1),
                "memory_mb": process.memory_info().rss / (1024 * 1024),
                "uptime_seconds": (datetime.now().timestamp() - process.create_time())
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {"cpu_percent": 0.0, "memory_mb": 0.0, "uptime_seconds": 0.0}

    def _find_process_by_port(self, port: int) -> Optional[int]:
        """Find process PID listening on a specific port."""
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN' and conn.laddr.port == port:
                return conn.pid
        return None

    def _find_process_by_script(self, script_name: str) -> Optional[int]:
        """Find process PID by script name in command line."""
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any(script_name in arg for arg in cmdline):
                    return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def get_agent_status(self, agent_name: str) -> ProcessInfo:
        """Get status of an agent. Auto-detects running processes even without PID file."""
        if agent_name not in self.AGENTS_CONFIG:
            raise ValueError(f"Unknown agent: {agent_name}")

        config = self.AGENTS_CONFIG[agent_name]
        pid = self._read_pid(agent_name)

        # Check if PID file exists and process is running
        if pid is not None and self._is_process_running(pid):
            stats = self._get_process_stats(pid)
            return ProcessInfo(
                pid=pid,
                name=agent_name,
                type="agent",
                status="running",
                port=config["port"],
                cpu_percent=stats["cpu_percent"],
                memory_mb=stats["memory_mb"],
                uptime_seconds=stats["uptime_seconds"],
                log_file=str(self._get_log_file(agent_name))
            )

        # PID file exists but process is dead - clean up
        if pid is not None:
            self._remove_pid(agent_name)

        # Try to find process by port (most reliable)
        port_pid = self._find_process_by_port(config["port"])
        if port_pid is not None:
            logger.info(f"Found {agent_name} running on port {config['port']} (PID: {port_pid}) - creating PID file")
            self._write_pid(agent_name, port_pid)
            stats = self._get_process_stats(port_pid)
            return ProcessInfo(
                pid=port_pid,
                name=agent_name,
                type="agent",
                status="running",
                port=config["port"],
                cpu_percent=stats["cpu_percent"],
                memory_mb=stats["memory_mb"],
                uptime_seconds=stats["uptime_seconds"],
                log_file=str(self._get_log_file(agent_name))
            )

        # Try to find process by script name (fallback)
        script_pid = self._find_process_by_script(config["script"])
        if script_pid is not None:
            logger.info(f"Found {agent_name} by script name (PID: {script_pid}) - creating PID file")
            self._write_pid(agent_name, script_pid)
            stats = self._get_process_stats(script_pid)
            return ProcessInfo(
                pid=script_pid,
                name=agent_name,
                type="agent",
                status="running",
                port=config["port"],
                cpu_percent=stats["cpu_percent"],
                memory_mb=stats["memory_mb"],
                uptime_seconds=stats["uptime_seconds"],
                log_file=str(self._get_log_file(agent_name))
            )

        # No process found
        return ProcessInfo(
            pid=0,
            name=agent_name,
            type="agent",
            status="stopped",
            port=config["port"],
            log_file=str(self._get_log_file(agent_name))
        )

    def get_all_agents_status(self) -> List[ProcessInfo]:
        """Get status of all agents."""
        return [
            self.get_agent_status(agent_name)
            for agent_name in self.AGENTS_CONFIG.keys()
        ]

    def start_agent(self, agent_name: str) -> ProcessInfo:
        """Start an agent process."""
        if agent_name not in self.AGENTS_CONFIG:
            raise ValueError(f"Unknown agent: {agent_name}")

        # Check if already running
        status = self.get_agent_status(agent_name)
        if status.status == "running":
            logger.warning(f"Agent {agent_name} is already running (PID: {status.pid})")
            return status

        config = self.AGENTS_CONFIG[agent_name]
        script_path = self.project_root / config["script"]
        log_file = self._get_log_file(agent_name)

        # Start process
        logger.info(f"Starting agent {agent_name} from {script_path}")

        # Set PYTHONPATH to project root for imports to work
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.project_root)

        with open(log_file, 'a') as log:
            process = subprocess.Popen(
                ["python", str(script_path)],
                cwd=str(self.project_root),
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True  # Detach from parent
            )

        self._write_pid(agent_name, process.pid)
        logger.info(f"Agent {agent_name} started with PID {process.pid}")

        return ProcessInfo(
            pid=process.pid,
            name=agent_name,
            type="agent",
            status="starting",
            port=config["port"],
            log_file=str(log_file)
        )

    def stop_agent(self, agent_name: str) -> ProcessInfo:
        """Stop an agent process."""
        if agent_name not in self.AGENTS_CONFIG:
            raise ValueError(f"Unknown agent: {agent_name}")

        status = self.get_agent_status(agent_name)

        if status.status == "stopped":
            logger.warning(f"Agent {agent_name} is not running")
            return status

        pid = status.pid
        logger.info(f"Stopping agent {agent_name} (PID: {pid})")

        try:
            process = psutil.Process(pid)
            # Try graceful shutdown first
            process.terminate()

            try:
                process.wait(timeout=5)  # Wait up to 5 seconds
                logger.info(f"Agent {agent_name} terminated gracefully")
            except psutil.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning(f"Agent {agent_name} did not terminate, forcing kill")
                process.kill()
                process.wait(timeout=5)
                logger.info(f"Agent {agent_name} killed forcefully")

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Error stopping agent {agent_name}: {e}")

        finally:
            self._remove_pid(agent_name)

        return ProcessInfo(
            pid=0,
            name=agent_name,
            type="agent",
            status="stopped",
            port=self.AGENTS_CONFIG[agent_name]["port"],
            log_file=str(self._get_log_file(agent_name))
        )

    def restart_agent(self, agent_name: str) -> ProcessInfo:
        """Restart an agent process."""
        logger.info(f"Restarting agent {agent_name}")
        self.stop_agent(agent_name)
        return self.start_agent(agent_name)

    def start_all_agents(self) -> List[ProcessInfo]:
        """Start all agents."""
        logger.info("Starting all agents")
        return [
            self.start_agent(agent_name)
            for agent_name in self.AGENTS_CONFIG.keys()
        ]

    def stop_all_agents(self) -> List[ProcessInfo]:
        """Stop all agents."""
        logger.info("Stopping all agents")
        return [
            self.stop_agent(agent_name)
            for agent_name in self.AGENTS_CONFIG.keys()
        ]

    def get_logs(self, name: str, lines: int = 50) -> List[str]:
        """Get last N lines from a process log file."""
        log_file = self._get_log_file(name)

        if not log_file.exists():
            return []

        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                return [line.rstrip() for line in all_lines[-lines:]]
        except IOError as e:
            logger.error(f"Error reading log file {log_file}: {e}")
            return []
