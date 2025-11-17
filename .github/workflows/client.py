#!/usr/bin/env python3
"""FastMCP client to test the deployed basic-agent server."""

import os
import sys
import asyncio
import json
from fastmcp import Client
from asyncio import TimeoutError, wait_for

TIMEOUT = 300

async def main():
    """Connect to MCP server and test the example_usage tool."""

    # Determine URL
    server_url = os.environ.get("MCP_APP_URL")
    if not server_url and len(sys.argv) > 1:
        server_url = sys.argv[1]

    if not server_url:
        print("❌ No MCP_APP_URL provided")
        return 1

    print(f"🔌 Connecting to MCP server at: {server_url}")

    # Build headers depending on auth availability
    api_key = os.environ.get("MCPAC_API_KEY")

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        print("🔐 Authentication enabled")
    else:
        print("🔓 No authentication (public server)")

    # Build FastMCP config
    config = {
        "mcpServers": {
            "basic_agent": {
                "transport": "sse",
                "url": server_url + "/sse",
                "headers": headers   # empty or authed
            }
        }
    }

    client = Client(config)

    try:
        async with client:
            print("🏓 Testing connection...")
            await client.ping()
            print("✅ Connected successfully!")

            # List tools, resources, prompts
            print("\n📋 Listing available operations...")
            tools = await client.list_tools()
            resources = await client.list_resources()
            prompts = await client.list_prompts()

            # Print available tools
            if tools:
                print("\nAvailable tools:")
                for tool in tools:
                    print(f" * {tool.name}: {tool.description}")
            else:
                print("No tools available")

            # Try example_usage or fallback
            tool_names = [tool.name for tool in tools] if tools else []

            if "example_usage" in tool_names:
                print("\n🔧 Calling example_usage tool...")

                try:
                    result = await wait_for(
                        client.call_tool("example_usage", {}),
                        timeout=TIMEOUT
                    )
                except TimeoutError:
                    print(f"⏱️ Tool call exceeded timeout of {TIMEOUT}s")
                    return 1

                print("📤 Response received")
                print(str(result)[:500])
                print("✅ Tool call completed successfully!")
                return 0

            else:
                print("❌ example_usage tool not found")
                print(f"Available tools: {tool_names}")

                if tool_names:
                    first = tool_names[0]
                    print(f"🔧 Trying fallback tool: {first}")

                    try:
                        result = await wait_for(
                            client.call_tool(first, {}),
                            timeout=TIMEOUT
                        )
                        print(str(result)[:500])
                        print("✅ Tool call completed successfully!")
                        return 0
                    except Exception as e:
                        print(f"⚠️ Fallback failed: {e}")
                        return 1
                else:
                    print("⚠️ No tools available")
                    return 1

    except Exception as e:
        print(f"❌ Client error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
