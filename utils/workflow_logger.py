"""
Workflow Execution Logger

Provides detailed logging to /tmp/editor-server.log for debugging workflows.
"""

import logging
from pathlib import Path
from typing import Any, Dict

# Create file logger
workflow_file_logger = logging.getLogger("workflow_file")
workflow_file_logger.setLevel(logging.DEBUG)

# Remove existing handlers
workflow_file_logger.handlers = []

# File handler for /tmp/editor-server.log
file_handler = logging.FileHandler('/tmp/editor-server.log', mode='a')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - WORKFLOW - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
workflow_file_logger.addHandler(file_handler)

# Prevent propagation to root logger
workflow_file_logger.propagate = False


def log_node_start(node_id: str, agent: str, retry: int, max_retries: int, instruction: str):
    """Log the start of node execution."""
    workflow_file_logger.info("=" * 80)
    workflow_file_logger.info(f"🚀 NODE START: {node_id}")
    workflow_file_logger.info(f"   Agent: {agent}")
    workflow_file_logger.info(f"   Retry: {retry}/{max_retries}")
    workflow_file_logger.info(f"   Instruction (first 200 chars):")
    workflow_file_logger.info(f"   {instruction[:200]}...")
    workflow_file_logger.info("=" * 80)


def log_node_complete(node_id: str, execution_time: float, output: str):
    """Log the completion of node execution."""
    workflow_file_logger.info("-" * 80)
    workflow_file_logger.info(f"✅ NODE COMPLETE: {node_id}")
    workflow_file_logger.info(f"   Execution time: {execution_time:.2f}s")
    workflow_file_logger.info(f"   Output length: {len(output)} chars")
    workflow_file_logger.info(f"   Output preview (first 500 chars):")
    workflow_file_logger.info(f"   {output[:500]}")
    if len(output) > 500:
        workflow_file_logger.info(f"   ... (truncated, {len(output) - 500} more chars)")
    workflow_file_logger.info("-" * 80)


def log_node_error(node_id: str, error: Exception):
    """Log node execution error."""
    workflow_file_logger.error("!" * 80)
    workflow_file_logger.error(f"❌ NODE ERROR: {node_id}")
    workflow_file_logger.error(f"   Error type: {type(error).__name__}")
    workflow_file_logger.error(f"   Error message: {str(error)}")
    workflow_file_logger.error("!" * 80)


def log_agent_invocation(agent_type: str, instruction: str):
    """Log agent invocation details."""
    workflow_file_logger.debug(f"🤖 AGENT INVOCATION: {agent_type}")
    workflow_file_logger.debug(f"   Full instruction:")
    workflow_file_logger.debug(f"   {instruction}")


def log_agent_response(agent_type: str, response: str):
    """Log agent response."""
    workflow_file_logger.debug(f"📨 AGENT RESPONSE: {agent_type}")
    workflow_file_logger.debug(f"   Response length: {len(response)} chars")
    workflow_file_logger.debug(f"   Full response:")
    workflow_file_logger.debug(f"   {response}")


def log_mcp_call(tool_name: str, arguments: Dict[str, Any]):
    """Log MCP tool call."""
    workflow_file_logger.info(f"🔧 MCP TOOL CALL: {tool_name}")
    workflow_file_logger.info(f"   Arguments: {arguments}")


def log_mcp_response(tool_name: str, response: Any):
    """Log MCP tool response."""
    workflow_file_logger.info(f"📦 MCP RESPONSE: {tool_name}")
    workflow_file_logger.info(f"   Response type: {type(response).__name__}")
    workflow_file_logger.info(f"   Response: {response}")


def log_conditional_evaluation(from_node: str, condition_result: bool, next_node: str):
    """Log conditional edge evaluation."""
    workflow_file_logger.info(f"🔀 CONDITIONAL: {from_node}")
    workflow_file_logger.info(f"   Condition result: {condition_result}")
    workflow_file_logger.info(f"   Next node: {next_node}")


def log_workflow_start(workflow_name: str, user_input: str, params: Dict[str, Any]):
    """Log workflow execution start."""
    workflow_file_logger.info("=" * 100)
    workflow_file_logger.info(f"🚀 WORKFLOW START: {workflow_name}")
    workflow_file_logger.info(f"   User input: {user_input}")
    workflow_file_logger.info(f"   Parameters: {params}")
    workflow_file_logger.info("=" * 100)


def log_workflow_complete(workflow_name: str, success: bool, message: str):
    """Log workflow execution completion."""
    workflow_file_logger.info("=" * 100)
    if success:
        workflow_file_logger.info(f"✅ WORKFLOW COMPLETE: {workflow_name}")
    else:
        workflow_file_logger.error(f"❌ WORKFLOW FAILED: {workflow_name}")
    workflow_file_logger.info(f"   Message: {message}")
    workflow_file_logger.info("=" * 100)
