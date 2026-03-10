"""
API module initialization.

This module exposes the registered routers for the application.
Currently, only chat_routes and kpi_routes are actively used.

Note: routes.py is kept for reference but not imported/registered
as it references non-existent configuration and is superseded by
the current chat_routes and kpi_routes implementation.
"""

# from .routes import api_router  # DISABLED: Dead code - references undefined 'settings'

__all__ = []  # No routers exported from this module; main.py imports routes directly
