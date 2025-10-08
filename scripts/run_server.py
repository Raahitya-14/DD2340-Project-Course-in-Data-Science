#!/usr/bin/env python3
"""Run the MCP Server"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.mcp_server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
