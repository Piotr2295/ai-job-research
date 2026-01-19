#!/usr/bin/env python3
"""
Test script for MCP Server

This script tests the MCP server functionality by simulating tool calls.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def test_mcp_server():
    """Test the MCP server by running it and checking if it starts correctly"""

    # Check if server.py exists
    server_path = Path(__file__).parent / "server.py"
    if not server_path.exists():
        print("❌ server.py not found")
        return False

    try:
        # Try to import the server module to check for syntax errors
        sys.path.insert(0, str(server_path.parent))
        import server

        # Check if the server has the required functions
        if not hasattr(server, 'handle_list_tools'):
            print("❌ handle_list_tools function not found")
            return False

        if not hasattr(server, 'handle_call_tool'):
            print("❌ handle_call_tool function not found")
            return False

        print("✅ MCP server module imported successfully")

        # Test database initialization
        try:
            server.init_database()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False

        # Test tool listing
        try:
            tools = await server.handle_list_tools()
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
        except Exception as e:
            print(f"❌ Tool listing failed: {e}")
            return False

        # Test a simple tool call (save_file_to_workspace)
        try:
            result = await server.handle_call_tool("save_file_to_workspace", {
                "filename": "test_output.txt",
                "content": "This is a test file created by the MCP server test."
            })
            print("✅ File save tool executed successfully")
            print(f"  Result: {result[0].text}")
        except Exception as e:
            print(f"❌ File save tool failed: {e}")
            return False

        # Test reading the file back
        try:
            result = await server.handle_call_tool("read_file_from_workspace", {
                "filename": "test_output.txt"
            })
            print("✅ File read tool executed successfully")
            print(f"  Content: {result[0].text[:50]}...")
        except Exception as e:
            print(f"❌ File read tool failed: {e}")
            return False

        print("\n🎉 All MCP server tests passed!")
        return True

    except ImportError as e:
        print(f"❌ Failed to import server module: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)