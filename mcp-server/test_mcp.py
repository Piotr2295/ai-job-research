#!/usr/bin/env python3
"""
Test script for MCP Server

This script tests the MCP server functionality by simulating tool calls.
"""

import asyncio
import sys
from pathlib import Path


async def test_mcp_server():
    """Test the MCP server by running it and checking if it starts correctly"""

    # Check if server.py exists
    server_path = Path(__file__).parent / "server.py"
    if not server_path.exists():
        print("[FAIL] server.py not found")
        return False

    try:
        # Try to import the server module to check for syntax errors
        sys.path.insert(0, str(server_path.parent))
        import server

        # Check if the server has the required attributes
        if not hasattr(server, "TOOL_HANDLERS"):
            print("[FAIL] TOOL_HANDLERS not found")
            return False

        print("[PASS] MCP server module imported successfully")

        # Test database initialization
        try:
            server.init_database()
            print("[PASS] Database initialized successfully")
        except Exception as e:
            print(f"[FAIL] Database initialization failed: {e}")
            return False

        # Test tool registry
        try:
            if not hasattr(server, "TOOL_HANDLERS"):
                print("[FAIL] TOOL_HANDLERS registry not found")
                return False

            tool_count = len(server.TOOL_HANDLERS)
            print(f"[PASS] Found {tool_count} tools in registry:")
            for tool_name in server.TOOL_HANDLERS.keys():
                print(f"  - {tool_name}")
        except Exception as e:
            print(f"[FAIL] Tool registry check failed: {e}")
            return False

        # Test implementation functions directly (bypass decorator)
        try:
            result = await server.save_file_to_workspace_impl(
                filename="test_output.txt",
                content="This is a test file created by the MCP server test.",
                directory="analyses",
            )
            print("[PASS] File save implementation executed successfully")
            print(f"  Result: {result}")
        except Exception as e:
            print(f"[FAIL] File save implementation failed: {e}")
            return False

        # Test reading the file back
        try:
            result = await server.read_file_from_workspace_impl(
                filename="test_output.txt", directory="analyses"
            )
            print("[PASS] File read implementation executed successfully")
            print(f"  Content: {result[:50]}...")
        except Exception as e:
            print(f"[FAIL] File read implementation failed: {e}")
            return False

        print("\n[SUCCESS] All MCP server tests passed!")
        return True

    except ImportError as e:
        print(f"[FAIL] Failed to import server module: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error during testing: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)
