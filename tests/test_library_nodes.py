"""
Tests for Library Node functionality in workflows.
"""

import pytest
import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from schemas.workflow_schemas import (
    WorkflowTemplate,
    WorkflowNode,
    WorkflowState
)
from workflows.engine import WorkflowEngine
from libraries.base import (
    library_tool,
    LibraryResponse,
    clear_registry,
    get_registered_libraries
)
from libraries.registry import LibraryRegistry, LibraryCapabilities
from libraries.executor import LibraryExecutor


class TestLibraryDecorator:
    """Test the @library_tool decorator."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def test_basic_decorator(self):
        """Test basic decorator functionality."""
        @library_tool(
            name="test_function",
            description="A test function",
            parameters={
                "param1": {"type": "string", "required": True},
                "param2": {"type": "integer", "required": False, "default": 10}
            }
        )
        def test_func(param1: str, param2: int = 10):
            return f"Result: {param1} - {param2}"

        # Check function is registered
        libs = get_registered_libraries()
        assert "test_library_nodes" in libs
        assert "test_function" in libs["test_library_nodes"]

        func = libs["test_library_nodes"]["test_function"]
        assert func.name == "test_function"
        assert func.description == "A test function"
        assert len(func.parameters) == 2

    def test_async_function(self):
        """Test decorator with async function."""
        @library_tool(
            name="async_test",
            timeout=5
        )
        async def async_func():
            await asyncio.sleep(0.1)
            return "async result"

        libs = get_registered_libraries()
        func = libs["test_library_nodes"]["async_test"]
        assert func.is_async is True
        assert func.timeout == 5

    def test_parameter_validation(self):
        """Test parameter validation in decorated functions."""
        @library_tool(
            parameters={
                "required_param": {"type": "string", "required": True},
                "optional_param": {"type": "integer", "required": False}
            }
        )
        def validated_func(required_param: str, optional_param: int = None):
            return f"{required_param}:{optional_param}"

        libs = get_registered_libraries()
        func = libs["test_library_nodes"]["validated_func"]

        # Test valid parameters
        valid_params = func.validate_parameters({
            "required_param": "test"
        })
        assert valid_params["required_param"] == "test"

        # Test missing required parameter
        with pytest.raises(Exception):
            func.validate_parameters({})


class TestLibraryRegistry:
    """Test the LibraryRegistry class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.registry = LibraryRegistry(
            libraries_dir=Path(self.temp_dir),
            auto_discover=False
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_discover_libraries(self):
        """Test library discovery."""
        # Create a test library directory
        lib_dir = Path(self.temp_dir) / "test_lib"
        lib_dir.mkdir()

        # Create config.yaml
        config_file = lib_dir / "config.yaml"
        config_file.write_text("""
name: test_lib
version: 1.0.0
description: Test library
capabilities: []
        """)

        # Discover libraries
        discovered = self.registry.discover_libraries()

        assert "test_lib" in discovered
        assert discovered["test_lib"].name == "test_lib"
        assert discovered["test_lib"].version == "1.0.0"

    def test_capability_validation(self):
        """Test capability-based access control."""
        # Create library requiring filesystem write
        lib_dir = Path(self.temp_dir) / "secure_lib"
        lib_dir.mkdir()

        config_file = lib_dir / "config.yaml"
        config_file.write_text("""
name: secure_lib
version: 1.0.0
description: Secure library
capabilities:
  - filesystem_write
        """)

        # Registry without write capability
        restricted_registry = LibraryRegistry(
            libraries_dir=Path(self.temp_dir),
            capabilities=LibraryCapabilities(filesystem_read=True),
            auto_discover=True
        )

        # Should not discover library without required capability
        assert "secure_lib" not in restricted_registry._loaded_libraries

        # Registry with write capability
        full_registry = LibraryRegistry(
            libraries_dir=Path(self.temp_dir),
            capabilities=LibraryCapabilities(filesystem_write=True),
            auto_discover=True
        )

        # Should discover library with required capability
        assert "secure_lib" in full_registry._loaded_libraries

    def test_allowlist_blocklist(self):
        """Test library allowlist/blocklist functionality."""
        # Set blocklist
        self.registry.set_blocklist(["dangerous_lib"])

        # Try to load blocklisted library
        result = self.registry.load_library("dangerous_lib")
        assert result is False

        # Set allowlist
        self.registry.set_allowlist(["safe_lib"])

        # Try to load non-allowlisted library
        result = self.registry.load_library("other_lib")
        assert result is False


class TestLibraryExecutor:
    """Test the LibraryExecutor class."""

    @pytest.mark.asyncio
    async def test_execute_library_node(self):
        """Test executing a library node."""
        clear_registry()

        # Register a test function
        @library_tool(
            name="test_exec",
            parameters={
                "input": {"type": "string", "required": True}
            }
        )
        def test_exec(input: str):
            return LibraryResponse(
                success=True,
                data=f"Processed: {input}"
            )

        # Create executor
        executor = LibraryExecutor()

        # Create test node
        node = WorkflowNode(
            id="test_node",
            agent="library",
            instruction="Test instruction",
            library_name="test_library_nodes",
            function_name="test_exec",
            function_params={"input": "test_value"}
        )

        # Create test state
        state = WorkflowState()

        # Execute node
        result = await executor.execute_library_node(node, state, {})

        assert result == "Processed: test_value"

    @pytest.mark.asyncio
    async def test_parameter_substitution(self):
        """Test parameter substitution from workflow state."""
        clear_registry()

        # Register a test function
        @library_tool(
            name="substitution_test",
            parameters={
                "param1": {"type": "string", "required": True},
                "param2": {"type": "string", "required": True}
            }
        )
        def substitution_test(param1: str, param2: str):
            return LibraryResponse(
                success=True,
                data=f"{param1}|{param2}"
            )

        executor = LibraryExecutor()

        # Create node with variable substitution
        node = WorkflowNode(
            id="sub_node",
            agent="library",
            instruction="Test",
            library_name="test_library_nodes",
            function_name="substitution_test",
            function_params={
                "param1": "{previous_node_output}",
                "param2": "{workflow_param}"
            }
        )

        # Create state with values
        state = WorkflowState(
            node_outputs={"previous_node": "output_value"},
            workflow_params={"workflow_param": "param_value"}
        )

        # Execute
        result = await executor.execute_library_node(node, state, {})

        assert result == "output_value|param_value"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in library execution."""
        clear_registry()

        # Register a function that raises an error
        @library_tool(name="error_func")
        def error_func():
            raise ValueError("Test error")

        executor = LibraryExecutor()

        node = WorkflowNode(
            id="error_node",
            agent="library",
            instruction="Test",
            library_name="test_library_nodes",
            function_name="error_func",
            function_params={}
        )

        state = WorkflowState()

        # Should raise LibraryError
        with pytest.raises(Exception) as exc_info:
            await executor.execute_library_node(node, state, {})

        assert "Test error" in str(exc_info.value)


class TestWorkflowWithLibraries:
    """Test full workflow execution with library nodes."""

    @pytest.mark.asyncio
    async def test_workflow_with_library_node(self):
        """Test a workflow that includes library nodes."""
        clear_registry()

        # Register test functions
        @library_tool(
            name="fetch_data",
            parameters={"source": {"type": "string", "required": True}}
        )
        def fetch_data(source: str):
            return LibraryResponse(
                success=True,
                data={"source": source, "data": "test_data"}
            )

        @library_tool(
            name="process_data",
            parameters={"data": {"type": "dict", "required": True}}
        )
        def process_data(data: dict):
            return LibraryResponse(
                success=True,
                data=f"Processed from {data.get('source', 'unknown')}"
            )

        # Create workflow template
        template = WorkflowTemplate(
            name="test_library_workflow",
            description="Test workflow with library nodes",
            nodes=[
                WorkflowNode(
                    id="fetch",
                    agent="library",
                    instruction="Fetch data from source",
                    library_name="test_library_nodes",
                    function_name="fetch_data",
                    function_params={"source": "api"}
                ),
                WorkflowNode(
                    id="process",
                    agent="library",
                    instruction="Process fetched data",
                    library_name="test_library_nodes",
                    function_name="process_data",
                    function_params={"data": "{fetch_output}"},
                    depends_on=["fetch"]
                )
            ]
        )

        # Execute workflow
        engine = WorkflowEngine(mode="custom")
        result = await engine.execute_workflow(
            template=template,
            user_input="Test workflow",
            params={}
        )

        assert result.success
        assert "Processed from api" in result.final_output

    @pytest.mark.asyncio
    async def test_mixed_workflow(self):
        """Test workflow with mixed agent types including libraries."""
        clear_registry()

        # Register a library function
        @library_tool(
            name="format_output",
            parameters={"text": {"type": "string", "required": True}}
        )
        def format_output(text: str):
            return LibraryResponse(
                success=True,
                data=f"FORMATTED: {text.upper()}"
            )

        template = WorkflowTemplate(
            name="mixed_workflow",
            description="Mixed agent workflow",
            nodes=[
                # Mock regular agent node
                WorkflowNode(
                    id="research",
                    agent="researcher",
                    instruction="Research the topic"
                ),
                # Library node that uses research output
                WorkflowNode(
                    id="format",
                    agent="library",
                    instruction="Format the research",
                    library_name="test_library_nodes",
                    function_name="format_output",
                    function_params={"text": "{research_output}"},
                    depends_on=["research"]
                )
            ]
        )

        # Mock the researcher agent
        with patch('workflows.engine.WorkflowEngine._execute_agent') as mock_agent:
            mock_agent.return_value = "research findings"

            engine = WorkflowEngine(mode="custom")
            result = await engine.execute_workflow(
                template=template,
                user_input="Test",
                params={}
            )

            assert result.success
            assert "FORMATTED: RESEARCH FINDINGS" in result.final_output


class TestRESTAPILibrary:
    """Test the REST API library."""

    @pytest.mark.asyncio
    async def test_http_get(self):
        """Test HTTP GET function."""
        from libraries.rest_api.client import http_get

        # Mock httpx client
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "data"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.url = "http://example.com"
            mock_response.raise_for_status = AsyncMock()

            mock_client.get.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client

            result = await http_get("http://example.com")

            assert result.success
            assert result.data == {"result": "data"}
            assert result.metadata["status_code"] == 200


class TestFilesystemLibrary:
    """Test the Filesystem library."""

    def test_read_write_file(self):
        """Test file read/write operations."""
        from libraries.filesystem.operations import read_file, write_file

        with tempfile.TemporaryDirectory() as tmpdir:
            # Override allowed paths for testing
            import libraries.filesystem.operations as ops
            original_paths = ops.ALLOWED_PATHS
            ops.ALLOWED_PATHS = [tmpdir]

            try:
                # Test write
                file_path = os.path.join(tmpdir, "test.txt")
                write_result = write_file(file_path, "test content")
                assert write_result.success

                # Test read
                read_result = read_file(file_path)
                assert read_result.success
                assert read_result.data == "test content"

            finally:
                # Restore original paths
                ops.ALLOWED_PATHS = original_paths

    def test_path_validation(self):
        """Test path validation security."""
        from libraries.filesystem.operations import read_file

        # Try to read outside allowed paths
        result = read_file("/etc/passwd")
        assert not result.success
        assert "not in allowed directories" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])