"""
MCP Quick Start Guide for TripPlanner
======================================

This file demonstrates how to integrate MCP servers into the TripPlanner application.
Start with the highest-priority integrations: File System, Memory, and Weather.

Installation:
-------------
1. Install MCP SDK:
   pip install mcp

2. Install Node.js MCP servers:
   npm install -g @modelcontextprotocol/server-filesystem
   npm install -g @modelcontextprotocol/server-memory
   npm install -g @modelcontextprotocol/server-weather

3. Set up environment variables in .env:
   OPENWEATHER_API_KEY=your_openweather_api_key
   MCP_STORAGE_PATH=./travel-plans
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# MCP imports
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    print("⚠️ MCP not installed. Run: pip install mcp")
    MCP_AVAILABLE = False

# LangChain imports
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from typing import Type


# ============================================================================
# MCP CLIENT MANAGER
# ============================================================================

class MCPManager:
    """Manages connections to multiple MCP servers"""

    def __init__(self):
        self.servers = {}
        self.sessions = {}
        self.initialized = False

    async def initialize_server(self, name: str, command: str, args: list, env: Dict[str, str] = None):
        """
        Initialize a connection to an MCP server

        Args:
            name: Server identifier (e.g., 'weather', 'filesystem')
            command: Command to run the server (e.g., 'npx')
            args: Command arguments
            env: Environment variables for the server
        """
        try:
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=env or {}
            )

            print(f"🔌 Initializing MCP server: {name}")

            # Note: In production, you'd want to keep these connections alive
            # This is a simplified example
            read, write = await stdio_client(server_params)
            session = ClientSession(read, write)

            await session.initialize()

            # List available tools
            tools_response = await session.list_tools()
            tools = tools_response.tools if hasattr(tools_response, 'tools') else []

            self.sessions[name] = session
            self.servers[name] = {
                "session": session,
                "tools": [tool.name for tool in tools],
                "params": server_params
            }

            print(f"✅ {name} server initialized with tools: {self.servers[name]['tools']}")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize {name} server: {e}")
            return False

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on an MCP server

        Args:
            server_name: Name of the server
            tool_name: Name of the tool to call
            arguments: Tool arguments as a dictionary

        Returns:
            Tool result
        """
        if server_name not in self.sessions:
            raise ValueError(f"Server {server_name} not initialized")

        session = self.sessions[server_name]

        try:
            result = await session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            print(f"❌ Error calling {tool_name} on {server_name}: {e}")
            raise

    async def cleanup(self):
        """Close all MCP server connections"""
        for name, session in self.sessions.items():
            try:
                await session.close()
                print(f"🔌 Closed connection to {name}")
            except Exception as e:
                print(f"⚠️ Error closing {name}: {e}")

# Global MCP manager instance
mcp_manager = MCPManager()


# ============================================================================
# CONFIGURATION
# ============================================================================

MCP_CONFIG = {
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem",
                 os.getenv("MCP_STORAGE_PATH", "./travel-plans")],
        "env": {}
    },
    "memory": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "env": {}
    },
    "weather": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-weather"],
        "env": {
            "OPENWEATHER_API_KEY": os.getenv("OPENWEATHER_API_KEY", "")
        }
    }
}


# ============================================================================
# MCP-POWERED LANGCHAIN TOOLS
# ============================================================================

# --- Input Schemas ---

class WeatherInput(BaseModel):
    city: str = Field(description="City name to get weather forecast for")
    days: int = Field(default=5, description="Number of days to forecast (1-7)")


class SavePlanInput(BaseModel):
    plan_data: dict = Field(description="Travel plan data to save")
    plan_name: Optional[str] = Field(None, description="Optional name for the plan")


class LoadPlanInput(BaseModel):
    plan_id: str = Field(description="ID of the plan to load")


class UserMemoryInput(BaseModel):
    user_id: str = Field(description="User identifier")
    key: str = Field(description="Memory key (e.g., 'food_preferences')")
    value: Optional[str] = Field(None, description="Value to store (if storing)")


# --- MCP Tools ---

class MCPWeatherTool(BaseTool):
    """Get weather forecasts using MCP weather server"""

    name: str = "check_weather"
    description: str = """
    Get real-time weather forecast for a city. Use this to recommend
    weather-appropriate activities and advise travelers on what to bring.
    Returns temperature, conditions, and multi-day forecasts.
    """
    args_schema: Type[BaseModel] = WeatherInput

    def _run(self, city: str, days: int = 5) -> str:
        """Synchronous wrapper"""
        return asyncio.run(self._arun(city, days))

    async def _arun(self, city: str, days: int = 5) -> str:
        """Get weather forecast asynchronously"""
        try:
            result = await mcp_manager.call_tool(
                "weather",
                "get_forecast",
                {
                    "city": city,
                    "days": min(days, 7)
                }
            )

            # Format the weather data
            return self._format_weather(result, city)

        except Exception as e:
            return f"❌ Unable to fetch weather for {city}: {str(e)}"

    def _format_weather(self, weather_data: Any, city: str) -> str:
        """Format weather data for display"""
        # This is a simplified formatter - adjust based on actual MCP response
        output = f"🌤️ WEATHER FORECAST for {city}:\n"
        output += "━" * 50 + "\n\n"

        if hasattr(weather_data, 'content'):
            # Extract content from MCP response
            for item in weather_data.content:
                if hasattr(item, 'text'):
                    output += item.text + "\n"
        else:
            output += str(weather_data)

        return output


class MCPSavePlanTool(BaseTool):
    """Save travel plans to persistent storage using MCP filesystem"""

    name: str = "save_travel_plan"
    description: str = """
    Save a travel plan to persistent storage. The plan can be retrieved later.
    Use this after generating a complete travel itinerary.
    """
    args_schema: Type[BaseModel] = SavePlanInput

    def _run(self, plan_data: dict, plan_name: Optional[str] = None) -> str:
        """Synchronous wrapper"""
        return asyncio.run(self._arun(plan_data, plan_name))

    async def _arun(self, plan_data: dict, plan_name: Optional[str] = None) -> str:
        """Save plan asynchronously"""
        try:
            # Generate plan ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            city = plan_data.get("city", "unknown")
            plan_id = f"{city}_{timestamp}"

            # Create filename
            filename = f"{plan_id}.json"

            # Prepare plan data with metadata
            full_plan = {
                "plan_id": plan_id,
                "plan_name": plan_name or f"{city} Trip",
                "created_at": datetime.now().isoformat(),
                "data": plan_data
            }

            # Save using filesystem MCP
            result = await mcp_manager.call_tool(
                "filesystem",
                "write_file",
                {
                    "path": filename,
                    "content": json.dumps(full_plan, indent=2)
                }
            )

            return f"✅ Travel plan saved successfully!\n📁 Plan ID: {plan_id}\n💾 Location: {filename}"

        except Exception as e:
            return f"❌ Failed to save travel plan: {str(e)}"


class MCPLoadPlanTool(BaseTool):
    """Load saved travel plans from storage"""

    name: str = "load_travel_plan"
    description: str = """
    Load a previously saved travel plan by its ID.
    Use this to retrieve and reference past itineraries.
    """
    args_schema: Type[BaseModel] = LoadPlanInput

    def _run(self, plan_id: str) -> str:
        """Synchronous wrapper"""
        return asyncio.run(self._arun(plan_id))

    async def _arun(self, plan_id: str) -> str:
        """Load plan asynchronously"""
        try:
            filename = f"{plan_id}.json"

            result = await mcp_manager.call_tool(
                "filesystem",
                "read_file",
                {"path": filename}
            )

            # Extract content from MCP response
            if hasattr(result, 'content'):
                for item in result.content:
                    if hasattr(item, 'text'):
                        plan_data = json.loads(item.text)
                        return f"✅ Loaded plan: {plan_data.get('plan_name')}\n\n{json.dumps(plan_data, indent=2)}"

            return str(result)

        except Exception as e:
            return f"❌ Failed to load travel plan: {str(e)}"


class MCPUserMemoryTool(BaseTool):
    """Store and retrieve user preferences using MCP memory"""

    name: str = "user_memory"
    description: str = """
    Store or retrieve user preferences and travel history.
    Use this to personalize recommendations based on past trips and preferences.
    """
    args_schema: Type[BaseModel] = UserMemoryInput

    def _run(self, user_id: str, key: str, value: Optional[str] = None) -> str:
        """Synchronous wrapper"""
        return asyncio.run(self._arun(user_id, key, value))

    async def _arun(self, user_id: str, key: str, value: Optional[str] = None) -> str:
        """Store or retrieve memory asynchronously"""
        try:
            memory_key = f"{user_id}:{key}"

            if value is not None:
                # Store memory
                result = await mcp_manager.call_tool(
                    "memory",
                    "store_memory",
                    {
                        "key": memory_key,
                        "value": value
                    }
                )
                return f"✅ Stored preference for {user_id}: {key} = {value}"
            else:
                # Retrieve memory
                result = await mcp_manager.call_tool(
                    "memory",
                    "retrieve_memory",
                    {"key": memory_key}
                )

                if hasattr(result, 'content'):
                    for item in result.content:
                        if hasattr(item, 'text'):
                            return f"📝 {user_id} - {key}: {item.text}"

                return str(result)

        except Exception as e:
            return f"❌ Memory operation failed: {str(e)}"


# ============================================================================
# INITIALIZATION AND SETUP
# ============================================================================

async def initialize_mcp_servers():
    """Initialize all configured MCP servers"""
    print("🚀 Initializing MCP servers...")

    for server_name, config in MCP_CONFIG.items():
        await mcp_manager.initialize_server(
            name=server_name,
            command=config["command"],
            args=config["args"],
            env=config["env"]
        )

    print("✅ All MCP servers initialized!")


def get_mcp_tools():
    """Get all MCP-powered tools for LangChain agent"""
    return [
        MCPWeatherTool(),
        MCPSavePlanTool(),
        MCPLoadPlanTool(),
        MCPUserMemoryTool()
    ]


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_weather_check():
    """Example: Get weather forecast"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Weather Forecast")
    print("="*60 + "\n")

    await initialize_mcp_servers()

    weather_tool = MCPWeatherTool()
    result = await weather_tool._arun("Delhi", days=3)
    print(result)


async def example_save_and_load_plan():
    """Example: Save and load a travel plan"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Save and Load Travel Plan")
    print("="*60 + "\n")

    await initialize_mcp_servers()

    # Create sample plan
    sample_plan = {
        "city": "Delhi",
        "days": 2,
        "budget": "mid-range",
        "itinerary": [
            {
                "day": 1,
                "places": ["Red Fort", "Jama Masjid"],
                "restaurants": ["Karim's"]
            }
        ]
    }

    # Save plan
    save_tool = MCPSavePlanTool()
    save_result = await save_tool._arun(sample_plan, "Delhi Weekend Trip")
    print(save_result)

    # Extract plan ID from result
    plan_id = save_result.split("Plan ID: ")[1].split("\n")[0] if "Plan ID:" in save_result else None

    if plan_id:
        print("\n--- Loading saved plan ---\n")
        load_tool = MCPLoadPlanTool()
        load_result = await load_tool._arun(plan_id)
        print(load_result)


async def example_user_memory():
    """Example: Store and retrieve user preferences"""
    print("\n" + "="*60)
    print("EXAMPLE 3: User Memory")
    print("="*60 + "\n")

    await initialize_mcp_servers()

    memory_tool = MCPUserMemoryTool()

    # Store preferences
    print("--- Storing user preferences ---")
    result1 = await memory_tool._arun("user_123", "food_preference", "vegetarian")
    print(result1)

    result2 = await memory_tool._arun("user_123", "budget_preference", "mid-range")
    print(result2)

    result3 = await memory_tool._arun("user_123", "visited_cities", "Delhi, Mumbai, Jaipur")
    print(result3)

    # Retrieve preferences
    print("\n--- Retrieving user preferences ---")
    result4 = await memory_tool._arun("user_123", "food_preference")
    print(result4)

    result5 = await memory_tool._arun("user_123", "budget_preference")
    print(result5)


async def run_all_examples():
    """Run all examples"""
    try:
        # Example 1: Weather
        await example_weather_check()

        # Example 2: File operations
        await example_save_and_load_plan()

        # Example 3: Memory
        await example_user_memory()

    finally:
        # Cleanup
        await mcp_manager.cleanup()


# ============================================================================
# INTEGRATION WITH EXISTING TRIPPLANNER
# ============================================================================

def integrate_with_agent():
    """
    Example of how to integrate MCP tools with the existing LangChain agent

    In your agent.py file, you would:

    1. Import this module:
       from mcp_quickstart_guide import initialize_mcp_servers, get_mcp_tools

    2. Initialize MCP servers at startup:
       asyncio.run(initialize_mcp_servers())

    3. Add MCP tools to your agent:
       from tools import tools  # Your existing tools
       mcp_tools = get_mcp_tools()
       all_tools = tools + mcp_tools

       agent = create_openai_tools_agent(llm, all_tools, travel_prompt)

    4. Update your travel prompt to mention new capabilities:
       - Weather forecasting
       - Plan persistence
       - User memory
    """
    pass


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    if not MCP_AVAILABLE:
        print("❌ MCP not available. Please install: pip install mcp")
        exit(1)

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║        TripPlanner MCP Integration - Quick Start Guide       ║
    ╚══════════════════════════════════════════════════════════════╝

    This script demonstrates MCP server integration with:
    ✅ Weather forecasting
    ✅ File system storage
    ✅ User memory/preferences

    Make sure you have:
    1. Installed MCP: pip install mcp
    2. Installed MCP servers: npm install -g @modelcontextprotocol/server-*
    3. Set OPENWEATHER_API_KEY in .env
    """)

    # Run examples
    asyncio.run(run_all_examples())

    print("\n" + "="*60)
    print("✅ All examples completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Review the code in this file")
    print("2. Add MCP tools to your existing agent.py")
    print("3. Update your travel planning prompt")
    print("4. Test with real travel planning requests")
    print("\nFor more information, see: MCP_IMPROVEMENT_ANALYSIS.md")
