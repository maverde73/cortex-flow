"""
DEPRECATED: Legacy configuration module.

This module is maintained for backward compatibility only.
New code should use the JSON-based configuration system:

    from config import load_config
    config = load_config()

This file now wraps the new system to provide backward compatibility.
All imports of `config.settings` will continue to work but will show
deprecation warnings.
"""

import warnings

# Show deprecation warning when importing this module directly
warnings.warn(
    "The 'config.py' module is deprecated. "
    "Please migrate to JSON-based configuration:\n"
    "  from config import load_config\n"
    "  config = load_config()",
    DeprecationWarning,
    stacklevel=2
)

# Import compatibility layer that wraps the new JSON config system
from config_compat import settings

# Export settings for backward compatibility
__all__ = ['settings']
