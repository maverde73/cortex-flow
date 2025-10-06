"""
Agent Service Registry

Provides service discovery and health monitoring for distributed agents.
Maintains a registry of available agents and their status.
"""

import httpx
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    agent_id: str
    url: str
    status: str = "unknown"  # unknown, healthy, unhealthy
    last_check: Optional[datetime] = None
    consecutive_failures: int = 0
    metadata: Dict = field(default_factory=dict)


class AgentRegistry:
    """
    Central registry for agent service discovery.

    Maintains a list of available agents and their health status.
    Provides methods to check which agents are currently available.
    """

    def __init__(self, health_check_timeout: float = 2.0):
        """
        Initialize the agent registry.

        Args:
            health_check_timeout: Timeout for health check requests in seconds
        """
        self._agents: Dict[str, AgentInfo] = {}
        self._health_check_timeout = health_check_timeout
        self._lock = asyncio.Lock()

    async def register(
        self,
        agent_id: str,
        url: str,
        check_health: bool = True
    ) -> bool:
        """
        Register an agent in the registry.

        Args:
            agent_id: Unique identifier for the agent
            url: Base URL of the agent server
            check_health: Whether to perform initial health check

        Returns:
            True if registration successful, False otherwise
        """
        async with self._lock:
            agent_info = AgentInfo(agent_id=agent_id, url=url)

            if check_health:
                is_healthy = await self._check_agent_health(agent_info)
                agent_info.status = "healthy" if is_healthy else "unhealthy"
            else:
                agent_info.status = "registered"

            self._agents[agent_id] = agent_info

            logger.info(
                f"Registered agent '{agent_id}' at {url} "
                f"(status: {agent_info.status})"
            )

            return agent_info.status in ["healthy", "registered"]

    async def unregister(self, agent_id: str):
        """Remove an agent from the registry."""
        async with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                logger.info(f"Unregistered agent '{agent_id}'")

    async def get_available_agents(self) -> List[str]:
        """
        Get list of currently healthy agents.

        Returns:
            List of agent IDs that are healthy
        """
        async with self._lock:
            return [
                agent_id
                for agent_id, info in self._agents.items()
                if info.status == "healthy"
            ]

    async def is_agent_available(self, agent_id: str) -> bool:
        """Check if a specific agent is available."""
        async with self._lock:
            agent = self._agents.get(agent_id)
            return agent is not None and agent.status == "healthy"

    async def get_agent_url(self, agent_id: str) -> Optional[str]:
        """Get the URL for a specific agent."""
        async with self._lock:
            agent = self._agents.get(agent_id)
            return agent.url if agent else None

    async def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """Get full information about an agent."""
        async with self._lock:
            return self._agents.get(agent_id)

    async def get_all_agents(self) -> Dict[str, AgentInfo]:
        """Get information about all registered agents."""
        async with self._lock:
            return self._agents.copy()

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health checks on all registered agents.

        Returns:
            Dictionary mapping agent_id to health status
        """
        results = {}

        async with self._lock:
            agents_to_check = list(self._agents.values())

        # Check all agents concurrently
        tasks = [
            self._check_and_update_agent(agent)
            for agent in agents_to_check
        ]

        health_results = await asyncio.gather(*tasks, return_exceptions=True)

        for agent, is_healthy in zip(agents_to_check, health_results):
            if isinstance(is_healthy, Exception):
                logger.error(f"Error checking {agent.agent_id}: {is_healthy}")
                results[agent.agent_id] = False
            else:
                results[agent.agent_id] = is_healthy

        return results

    async def _check_and_update_agent(self, agent: AgentInfo) -> bool:
        """Check agent health and update its status."""
        is_healthy = await self._check_agent_health(agent)

        async with self._lock:
            if agent.agent_id in self._agents:
                if is_healthy:
                    self._agents[agent.agent_id].status = "healthy"
                    self._agents[agent.agent_id].consecutive_failures = 0
                else:
                    self._agents[agent.agent_id].consecutive_failures += 1
                    if self._agents[agent.agent_id].consecutive_failures >= 3:
                        self._agents[agent.agent_id].status = "unhealthy"

                self._agents[agent.agent_id].last_check = datetime.now()

        return is_healthy

    async def _check_agent_health(self, agent: AgentInfo) -> bool:
        """
        Perform health check on an agent.

        Args:
            agent: AgentInfo to check

        Returns:
            True if agent is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(
                timeout=self._health_check_timeout
            ) as client:
                response = await client.get(f"{agent.url}/health")

                if response.status_code == 200:
                    # Update metadata with health response
                    try:
                        health_data = response.json()
                        agent.metadata.update(health_data)
                    except:
                        pass

                    return True
                else:
                    logger.warning(
                        f"Agent {agent.agent_id} returned status "
                        f"{response.status_code}"
                    )
                    return False

        except httpx.ConnectError:
            logger.debug(f"Agent {agent.agent_id} connection refused")
            return False
        except httpx.TimeoutException:
            logger.debug(f"Agent {agent.agent_id} health check timed out")
            return False
        except Exception as e:
            logger.error(f"Error checking {agent.agent_id}: {e}")
            return False


# Global registry instance
_global_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get or create the global agent registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


async def initialize_registry_from_config():
    """
    Initialize the registry with agents from configuration.

    This should be called at application startup to register
    all configured agents.
    """
    from config import settings

    registry = get_registry()

    # Define available agents with their URLs
    agents_config = {
        "researcher": settings.researcher_url,
        "analyst": settings.analyst_url,
        "writer": settings.writer_url,
    }

    # Filter by enabled agents
    enabled = settings.enabled_agents

    for agent_id, url in agents_config.items():
        if agent_id in enabled:
            await registry.register(
                agent_id=agent_id,
                url=url,
                check_health=True
            )
            logger.info(f"Registered {agent_id} from configuration")

    # Log summary
    available = await registry.get_available_agents()
    logger.info(
        f"Registry initialized with {len(available)}/{len(enabled)} "
        f"agents available: {available}"
    )
