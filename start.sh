#!/bin/bash
# Quick launcher for Sionna AI Agent

echo " Sionna AI Agent"
echo "===================="
echo ""
echo "Restarting MCP server..."
pkill -f "src/mcp_http_server.py" 2>/dev/null || true
sleep 1

echo "Starting chat interface..."
echo "Open http://localhost:7860 in your browser"
echo ""

python3 app.py
