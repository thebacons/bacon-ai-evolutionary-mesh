#!/bin/bash
#
# BACON MQTT MCP Server - Installation Script
#
# This script:
# 1. Installs Python dependencies
# 2. Installs the package in editable mode
# 3. Copies agent definition to Claude Code
# 4. Provides guidance on settings.json configuration
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_AGENTS_DIR="$HOME/.claude/agents"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"

echo "========================================"
echo "BACON MQTT MCP Server - Installation"
echo "========================================"
echo ""

# Step 1: Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "❌ Python 3.10+ required. Found: $PYTHON_VERSION"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION"

# Step 2: Install dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install --break-system-packages -e "$SCRIPT_DIR" || pip install -e "$SCRIPT_DIR"
echo "✅ Dependencies installed"

# Step 3: Test import
echo ""
echo "🔧 Verifying installation..."
python3 -c "from bacon_mqtt_mcp.server import mcp; print('✅ Module imports OK')"

# Step 4: Copy agent definition
echo ""
echo "📁 Setting up Claude Code agent..."
mkdir -p "$CLAUDE_AGENTS_DIR"
cp "$SCRIPT_DIR/agents/mqtt-listener.md" "$CLAUDE_AGENTS_DIR/"
echo "✅ Agent definition copied to $CLAUDE_AGENTS_DIR/mqtt-listener.md"

# Step 5: Settings configuration
echo ""
echo "========================================"
echo "⚙️  Claude Code Configuration"
echo "========================================"
echo ""
echo "Add this to your ~/.claude/settings.json:"
echo ""
echo '  "env": {'
echo '    "MCP_TIMEOUT": "3600000",'
echo '    "MCP_TOOL_TIMEOUT": "3600000"'
echo '  },'
echo '  "mcpServers": {'
echo '    "bacon-mqtt": {'
echo '      "command": "python",'
echo '      "args": ["-m", "bacon_mqtt_mcp"],'
echo '      "timeout": 3600000,'
echo '      "env": {'
echo '        "MQTT_BROKER": "srv906866.hstgr.cloud",'
echo '        "MQTT_PORT": "1883"'
echo '      }'
echo '    }'
echo '  }'
echo ""

# Check if settings.json exists
if [ -f "$CLAUDE_SETTINGS" ]; then
    echo "📝 Found existing settings at: $CLAUDE_SETTINGS"
    echo "   Please merge the configuration manually."
else
    echo "📝 No settings.json found at: $CLAUDE_SETTINGS"
    echo "   You may need to create it or configure via Claude Code."
fi

# Step 6: Test MQTT connectivity
echo ""
echo "========================================"
echo "🔌 Testing MQTT Connectivity"
echo "========================================"
python3 "$SCRIPT_DIR/test_mqtt.py" --quick || {
    echo ""
    echo "⚠️  MQTT connectivity test failed."
    echo "   This might be expected if the broker is not reachable."
    echo "   You can run the full test later with:"
    echo "   python3 $SCRIPT_DIR/test_mqtt.py"
}

echo ""
echo "========================================"
echo "✅ Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Update ~/.claude/settings.json with the MCP server config"
echo "2. Restart Claude Code to load the new MCP server"
echo "3. Test with: 'Show status of bacon-mqtt MCP server'"
echo "4. Spawn listener: 'Run mqtt-listener agent in the background'"
echo ""
echo "For full testing:"
echo "  python3 $SCRIPT_DIR/test_mqtt.py"
echo ""
