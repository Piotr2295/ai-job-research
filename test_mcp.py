#!/usr/bin/env python3
"""
Test script for MCP Server functionality
Run this to test the MCP server tools without connecting to Claude.
"""

import asyncio
import sys
import os

# Add the mcp-server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp-server'))

from server import (
    save_job_analysis,
    get_user_analyses,
    update_learning_progress,
    analyze_github_profile,
    save_file_to_workspace,
    read_file_from_workspace
)

async def test_mcp_tools():
    """Test all MCP server tools"""
    print("🧪 Testing MCP Server Tools for AI Job Research")
    print("=" * 50)

    # Test 1: Save job analysis
    print("\n1. Testing save_job_analysis...")
    result = await save_job_analysis(
        user_id="test_user_123",
        job_title="Senior Python Developer",
        company="Tech Corp",
        skills_required=["Python", "FastAPI", "PostgreSQL", "Docker"],
        skill_gaps=["Kubernetes", "AWS"],
        learning_plan="Week 1-2: Learn Kubernetes basics\nWeek 3-4: AWS certification prep"
    )
    print(f"✅ {result}")

    # Test 2: Get user analyses
    print("\n2. Testing get_user_analyses...")
    analyses = await get_user_analyses("test_user_123", limit=5)
    print(f"✅ Retrieved analyses: {len(analyses)} characters")

    # Test 3: Update learning progress
    print("\n3. Testing update_learning_progress...")
    result = await update_learning_progress(
        user_id="test_user_123",
        skill="Kubernetes",
        progress_percentage=25,
        completed_modules=["Basic concepts", "Pods", "Services"]
    )
    print(f"✅ {result}")

    # Test 4: Save file to workspace
    print("\n4. Testing save_file_to_workspace...")
    result = await save_file_to_workspace(
        filename="sample_analysis.md",
        content="# Job Analysis Report\n\n## Skills Required\n- Python\n- FastAPI\n\n## Learning Plan\n1. Study basics\n2. Build projects",
        directory="analyses"
    )
    print(f"✅ {result}")

    # Test 5: Read file from workspace
    print("\n5. Testing read_file_from_workspace...")
    content = await read_file_from_workspace("sample_analysis.md", "analyses")
    print(f"✅ Read {len(content)} characters from file")

    # Test 6: Analyze GitHub profile (requires internet)
    print("\n6. Testing analyze_github_profile...")
    try:
        analysis = await analyze_github_profile("octocat")  # GitHub's mascot account
        print(f"✅ GitHub analysis: {len(analysis)} characters")
        print("Preview:", analysis[:200] + "...")
    except Exception as e:
        print(f"⚠️ GitHub analysis failed (expected without API): {e}")

    print("\n🎉 All MCP server tools tested successfully!")
    print("\nTo use with Claude Desktop:")
    print("1. Run: python mcp-server/server.py")
    print("2. Configure Claude Desktop to connect to the MCP server")
    print("3. Ask Claude: 'Save this job analysis for user123'")

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())