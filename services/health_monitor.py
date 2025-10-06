"""
Health Monitoring Service

Provides continuous health monitoring for registered agents with
automatic retry and recovery mechanisms.
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

from services.registry import get_registry

logger = logging.getLogger(__name__)


class HealthMonitor:
    """
    Monitors the health of registered agents continuously.

    Performs periodic health checks and maintains agent availability status.
    """

    def __init__(
        self,
        check_interval: float = 30.0,
        auto_start: bool = False
    ):
        """
        Initialize the health monitor.

        Args:
            check_interval: Seconds between health checks
            auto_start: Whether to start monitoring automatically
        """
        self.check_interval = check_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._registry = get_registry()

        if auto_start:
            asyncio.create_task(self.start())

    async def start(self):
        """Start the health monitoring loop."""
        if self._running:
            logger.warning("Health monitor already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(
            f"Health monitor started (interval: {self.check_interval}s)"
        )

    async def stop(self):
        """Stop the health monitoring loop."""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Health monitor stopped")

    async def _monitor_loop(self):
        """Main monitoring loop that runs continuously."""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
                # Continue monitoring despite errors
                await asyncio.sleep(self.check_interval)

    async def _perform_health_checks(self):
        """Perform health checks on all registered agents."""
        try:
            results = await self._registry.health_check_all()

            # Log status changes
            for agent_id, is_healthy in results.items():
                agent_info = await self._registry.get_agent_info(agent_id)

                if agent_info:
                    previous_status = agent_info.status

                    if is_healthy and previous_status != "healthy":
                        logger.info(f"Agent '{agent_id}' is now healthy")
                    elif not is_healthy and previous_status == "healthy":
                        logger.warning(f"Agent '{agent_id}' is now unhealthy")

        except Exception as e:
            logger.error(f"Error performing health checks: {e}")


# Global monitor instance
_global_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get or create the global health monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        from config_legacy import settings
        _global_monitor = HealthMonitor(
            check_interval=settings.agent_health_check_interval
        )
    return _global_monitor


async def start_health_monitoring():
    """Start the global health monitor."""
    monitor = get_health_monitor()
    await monitor.start()


async def stop_health_monitoring():
    """Stop the global health monitor."""
    monitor = get_health_monitor()
    await monitor.stop()
