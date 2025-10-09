"""
Library Registry and Loader

This module handles:
- Discovery of available libraries
- Dynamic loading of library modules
- Validation of library interfaces
- Caching loaded libraries
- Permission and capability management
"""

import os
import sys
import importlib
import importlib.util
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field

from libraries.base import (
    LibraryFunction,
    LibraryMetadata,
    LibraryError,
    get_library_function,
    clear_registry
)

logger = logging.getLogger(__name__)


@dataclass
class LibraryCapabilities:
    """Defines capabilities that libraries can require."""
    filesystem_read: bool = False
    filesystem_write: bool = False
    network_access: bool = False
    system_commands: bool = False
    database_access: bool = False
    email_access: bool = False
    custom_capabilities: Set[str] = field(default_factory=set)

    def has_capability(self, capability: str) -> bool:
        """Check if a capability is granted."""
        if hasattr(self, capability):
            return getattr(self, capability)
        return capability in self.custom_capabilities

    def validate_required(self, required: List[str]) -> bool:
        """Validate that all required capabilities are granted."""
        return all(self.has_capability(cap) for cap in required)


class LibraryRegistry:
    """
    Manages library discovery, loading, and access control.
    """

    def __init__(
        self,
        libraries_dir: Optional[Path] = None,
        capabilities: Optional[LibraryCapabilities] = None,
        auto_discover: bool = True
    ):
        """
        Initialize the library registry.

        Args:
            libraries_dir: Directory containing libraries (defaults to ./libraries)
            capabilities: Granted capabilities for libraries
            auto_discover: Whether to automatically discover libraries on init
        """
        self.libraries_dir = libraries_dir or Path(__file__).parent
        self.capabilities = capabilities or LibraryCapabilities()
        self._loaded_libraries: Dict[str, LibraryMetadata] = {}
        self._library_functions: Dict[str, Dict[str, LibraryFunction]] = {}
        self._blocklist: Set[str] = set()
        self._allowlist: Optional[Set[str]] = None  # None means all allowed

        if auto_discover:
            self.discover_libraries()

    def discover_libraries(self) -> Dict[str, LibraryMetadata]:
        """
        Discover all available libraries in the libraries directory.

        Returns:
            Dictionary mapping library names to their metadata
        """
        discovered = {}

        # Ensure libraries directory exists
        if not self.libraries_dir.exists():
            logger.warning(f"Libraries directory not found: {self.libraries_dir}")
            return discovered

        # Scan for library directories
        for item in self.libraries_dir.iterdir():
            if item.is_dir() and not item.name.startswith('__'):
                # Check for config.yaml
                config_file = item / "config.yaml"

                if config_file.exists():
                    try:
                        with open(config_file, 'r') as f:
                            config = yaml.safe_load(f)

                        metadata = LibraryMetadata(**config)

                        # Validate capabilities
                        if not self.capabilities.validate_required(metadata.capabilities):
                            logger.warning(
                                f"Library '{item.name}' requires capabilities "
                                f"{metadata.capabilities} which are not granted"
                            )
                            continue

                        discovered[item.name] = metadata
                        logger.info(f"Discovered library: {item.name}")

                    except Exception as e:
                        logger.error(f"Error loading config for '{item.name}': {e}")
                else:
                    # Create default metadata for libraries without config
                    discovered[item.name] = LibraryMetadata(
                        name=item.name,
                        description=f"Library: {item.name}"
                    )
                    logger.info(f"Discovered library without config: {item.name}")

        self._loaded_libraries = discovered
        return discovered

    def load_library(self, library_name: str) -> bool:
        """
        Load a specific library module.

        Args:
            library_name: Name of the library to load

        Returns:
            True if loaded successfully, False otherwise
        """
        # Check blocklist/allowlist
        if library_name in self._blocklist:
            logger.warning(f"Library '{library_name}' is blocklisted")
            return False

        if self._allowlist is not None and library_name not in self._allowlist:
            logger.warning(f"Library '{library_name}' is not in allowlist")
            return False

        # Check if library exists
        library_path = self.libraries_dir / library_name

        if not library_path.exists():
            logger.error(f"Library directory not found: {library_path}")
            return False

        try:
            # Add library path to sys.path temporarily
            sys.path.insert(0, str(self.libraries_dir))

            # Import the library module
            module = importlib.import_module(library_name)

            # Look for library tools in the module
            functions_found = 0

            for name in dir(module):
                obj = getattr(module, name)
                if hasattr(obj, '_is_library_tool'):
                    functions_found += 1

            logger.info(
                f"Loaded library '{library_name}' with {functions_found} functions"
            )

            # Store functions from registry
            from libraries.base import get_registered_libraries
            all_funcs = get_registered_libraries()

            if library_name in all_funcs:
                self._library_functions[library_name] = all_funcs[library_name]

            return True

        except Exception as e:
            logger.error(f"Error loading library '{library_name}': {e}")
            return False

        finally:
            # Remove from sys.path
            if str(self.libraries_dir) in sys.path:
                sys.path.remove(str(self.libraries_dir))

    def load_all_libraries(self) -> int:
        """
        Load all discovered libraries.

        Returns:
            Number of successfully loaded libraries
        """
        loaded_count = 0

        for library_name in self._loaded_libraries:
            if self.load_library(library_name):
                loaded_count += 1

        logger.info(f"Loaded {loaded_count}/{len(self._loaded_libraries)} libraries")
        return loaded_count

    def get_library_function(
        self,
        library_name: str,
        function_name: str
    ) -> Optional[LibraryFunction]:
        """
        Get a specific library function.

        Args:
            library_name: Name of the library
            function_name: Name of the function

        Returns:
            LibraryFunction if found, None otherwise
        """
        # Try to load library if not already loaded
        if library_name not in self._library_functions:
            if not self.load_library(library_name):
                return None

        return self._library_functions.get(library_name, {}).get(function_name)

    def list_functions(self, library_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List available functions.

        Args:
            library_name: Optional library name to filter by

        Returns:
            Dictionary mapping library names to function names
        """
        if library_name:
            if library_name in self._library_functions:
                return {library_name: list(self._library_functions[library_name].keys())}
            else:
                return {}

        result = {}
        for lib_name, functions in self._library_functions.items():
            result[lib_name] = list(functions.keys())

        return result

    def set_blocklist(self, libraries: List[str]):
        """Set libraries that should not be loaded."""
        self._blocklist = set(libraries)
        logger.info(f"Set blocklist: {self._blocklist}")

    def set_allowlist(self, libraries: Optional[List[str]]):
        """Set libraries that are allowed (None means all allowed)."""
        self._allowlist = set(libraries) if libraries else None
        logger.info(f"Set allowlist: {self._allowlist}")

    def get_metadata(self, library_name: str) -> Optional[LibraryMetadata]:
        """Get metadata for a specific library."""
        return self._loaded_libraries.get(library_name)

    def validate_library(self, library_name: str) -> bool:
        """
        Validate that a library is properly structured and loadable.

        Args:
            library_name: Name of the library to validate

        Returns:
            True if valid, False otherwise
        """
        library_path = self.libraries_dir / library_name

        # Check directory exists
        if not library_path.exists():
            logger.error(f"Library directory not found: {library_path}")
            return False

        # Check for __init__.py
        init_file = library_path / "__init__.py"
        if not init_file.exists():
            logger.error(f"Library missing __init__.py: {library_name}")
            return False

        # Try to load and check for functions
        if self.load_library(library_name):
            functions = self._library_functions.get(library_name, {})
            if not functions:
                logger.warning(f"Library '{library_name}' has no registered functions")

            return True

        return False

    def clear_cache(self):
        """Clear all cached libraries and functions."""
        self._library_functions.clear()
        clear_registry()
        logger.info("Cleared library cache")


# Global registry instance
_global_registry: Optional[LibraryRegistry] = None


def get_library_registry(
    libraries_dir: Optional[Path] = None,
    capabilities: Optional[LibraryCapabilities] = None,
    reset: bool = False
) -> LibraryRegistry:
    """
    Get or create the global library registry.

    Args:
        libraries_dir: Directory containing libraries
        capabilities: Granted capabilities
        reset: Whether to reset the existing registry

    Returns:
        LibraryRegistry instance
    """
    global _global_registry

    if reset or _global_registry is None:
        _global_registry = LibraryRegistry(
            libraries_dir=libraries_dir,
            capabilities=capabilities
        )

    return _global_registry