"""
BACON MQTT MCP Server

Cross-machine Claude wake system using MQTT and MCP progress notifications.
"""

from .server import mcp, wait_for_message, send_message, check_messages, get_status

__version__ = "1.0.0"
__all__ = ["mcp", "wait_for_message", "send_message", "check_messages", "get_status"]
