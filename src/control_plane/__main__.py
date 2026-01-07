"""
Entry point for running bacon-mqtt-mcp as a module.

Usage:
    python -m bacon_mqtt_mcp
"""

from server import mcp

if __name__ == "__main__":
    mcp.run()
