"""
MCP Integration Module for TripPlanner
=======================================

Integrates Model Context Protocol servers with caching and rate limiting.

Includes:
- Weather MCP with 3-hour cache
- File System MCP for plan persistence
- Memory MCP for user preferences
- Automatic rate limiting
- Graceful fallbacks
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import cache manager
from cache_manager import cache_manager, rate_limited_api_call

# MCP imports with fallback
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    logger.warning("MCP not installed. Run: pip install mcp")
    MCP_AVAILABLE = False

# LangChain imports
try:
    from pydantic import BaseModel, Field
    from langchain.tools import BaseTool
    from typing import Type
    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain not available")
    LANGCHAIN_AVAILABLE = False


# ============================================================================
# MCP MANAGER WITH CACHING
# ============================================================================

class MCPManager:
    """
    Manages MCP server connections with automatic caching and rate limiting
    """

    def __init__(self):
        self.servers = {}
        self.sessions = {}
        self.initialized = False
        self.connection_lock = asyncio.Lock()

    async def initialize_server(
        self,
        name: str,
        command: str,
        args: List[str],
        env: Dict[str, str] = None
    ) -> bool:
        """
        Initialize an MCP server connection

        Args:
            name: Server identifier
            command: Command to run server
            args: Command arguments
            env: Environment variables

        Returns:
            True if successful, False otherwise
        """
        async with self.connection_lock:
            if name in self.sessions:
                logger.info(f"Server {name} already initialized")
                return True

            try:
                server_params = StdioServerParameters(
                    command=command,
                    args=args,
                    env=env or {}
                )

                logger.info(f"🔌 Initializing MCP server: {name}")

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
                    "params": server_params,
                    "initialized_at": datetime.now().isoformat()
                }

                logger.info(f"✅ {name} initialized with tools: {self.servers[name]['tools']}")
                return True

            except Exception as e:
                logger.error(f"❌ Failed to initialize {name}: {e}")
                return False

    async def call_tool_with_cache(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        cache_category: Optional[str] = None,
        bypass_cache: bool = False
    ) -> Any:
        """
        Call an MCP tool with automatic caching

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool
            arguments: Tool arguments
            cache_category: Cache category (defaults to server_name)
            bypass_cache: Skip cache and force API call

        Returns:
            Tool result
        """
        cache_category = cache_category or server_name

        # Try cache first (unless bypassed)
        if not bypass_cache:
            cached_result = cache_manager.get(
                cache_category,
                tool=tool_name,
                **arguments
            )
            if cached_result is not None:
                logger.info(f"Cache hit: {server_name}.{tool_name}")
                return cached_result

        # Check rate limit
        if not cache_manager.check_rate_limit(server_name):
            status = cache_manager.get_rate_limit_status(server_name)
            logger.warning(
                f"Rate limit exceeded for {server_name}: "
                f"{status['calls_used']}/{status['limit']} calls used"
            )
            # Return cached data if available, even if expired
            cached_result = cache_manager.get(
                cache_category,
                tool=tool_name,
                **arguments
            )
            if cached_result is not None:
                logger.info(f"Returning stale cache due to rate limit: {server_name}.{tool_name}")
                return cached_result

            raise Exception(
                f"Rate limit exceeded for {server_name}. "
                f"Resets in {status['reset_in']} seconds."
            )

        # Make API call
        try:
            if server_name not in self.sessions:
                raise ValueError(f"Server {server_name} not initialized")

            session = self.sessions[server_name]

            # Record API call for rate limiting
            cache_manager.record_api_call(server_name)

            result = await session.call_tool(tool_name, arguments)

            # Cache the result
            cache_manager.set(
                cache_category,
                result,
                tool=tool_name,
                **arguments
            )

            logger.info(f"API call successful: {server_name}.{tool_name}")
            return result

        except Exception as e:
            logger.error(f"Error calling {server_name}.{tool_name}: {e}")
            raise

    async def cleanup(self):
        """Close all MCP connections"""
        for name, session in self.sessions.items():
            try:
                # Note: MCP sessions may not have close() method
                # Just clear the reference
                logger.info(f"🔌 Closing connection to {name}")
            except Exception as e:
                logger.warning(f"Error closing {name}: {e}")

        self.sessions.clear()
        self.servers.clear()


# Global MCP manager
mcp_manager = MCPManager()


# ============================================================================
# MCP CONFIGURATION
# ============================================================================

def get_mcp_config() -> Dict:
    """Get MCP server configuration"""
    return {
        "filesystem": {
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                os.getenv("MCP_STORAGE_PATH", "./travel-plans")
            ],
            "env": {},
            "enabled": True
        },
        "memory": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"],
            "env": {},
            "enabled": True
        },
        "weather": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-weather"],
            "env": {
                "OPENWEATHER_API_KEY": os.getenv("OPENWEATHER_API_KEY", "")
            },
            "enabled": bool(os.getenv("OPENWEATHER_API_KEY"))
        }
    }


async def initialize_mcp_servers() -> Dict[str, bool]:
    """
    Initialize all configured MCP servers

    Returns:
        Dictionary mapping server names to initialization status
    """
    if not MCP_AVAILABLE:
        logger.error("MCP SDK not available")
        return {}

    logger.info("🚀 Initializing MCP servers...")

    config = get_mcp_config()
    results = {}

    for server_name, server_config in config.items():
        if not server_config.get("enabled", True):
            logger.info(f"⏭️ Skipping {server_name} (disabled)")
            results[server_name] = False
            continue

        success = await mcp_manager.initialize_server(
            name=server_name,
            command=server_config["command"],
            args=server_config["args"],
            env=server_config.get("env", {})
        )
        results[server_name] = success

    # Log summary
    successful = sum(1 for v in results.values() if v)
    total = len(results)
    logger.info(f"✅ MCP initialization complete: {successful}/{total} servers ready")

    return results


# ============================================================================
# LANGCHAIN TOOLS WITH MCP + CACHING
# ============================================================================

if LANGCHAIN_AVAILABLE:

    # --- Input Schemas ---

    class WeatherInput(BaseModel):
        city: str = Field(description="City name")
        days: int = Field(default=5, description="Forecast days (1-7)")

    class SavePlanInput(BaseModel):
        plan_data: dict = Field(description="Travel plan to save")
        plan_name: Optional[str] = Field(None, description="Plan name")

    class LoadPlanInput(BaseModel):
        plan_id: str = Field(description="Plan ID to load")

    class ListPlansInput(BaseModel):
        limit: int = Field(default=10, description="Max plans to return")

    class UserMemoryInput(BaseModel):
        user_id: str = Field(description="User identifier")
        key: str = Field(description="Memory key")
        value: Optional[str] = Field(None, description="Value to store")

    # --- MCP-Powered Tools ---

    class MCPWeatherTool(BaseTool):
        """Weather forecasts with 3-hour caching"""

        name: str = "check_weather"
        description: str = """Get weather forecast for travel planning.
        Automatically cached for 3 hours to minimize API calls.
        Returns temperature, conditions, and multi-day forecasts."""
        args_schema: Type[BaseModel] = WeatherInput

        def _run(self, city: str, days: int = 5) -> str:
            return asyncio.run(self._arun(city, days))

        async def _arun(self, city: str, days: int = 5) -> str:
            try:
                result = await mcp_manager.call_tool_with_cache(
                    "weather",
                    "get_forecast",
                    {"city": city, "days": min(days, 7)},
                    cache_category="weather"
                )
                return self._format_weather(result, city)
            except Exception as e:
                logger.error(f"Weather tool error: {e}")
                return f"❌ Unable to fetch weather for {city}: {str(e)}"

        def _format_weather(self, weather_data: Any, city: str) -> str:
            """Format weather response"""
            output = f"🌤️ WEATHER FORECAST for {city}:\n"
            output += "━" * 50 + "\n\n"

            if hasattr(weather_data, 'content'):
                for item in weather_data.content:
                    if hasattr(item, 'text'):
                        output += item.text + "\n"
            else:
                output += str(weather_data)

            output += f"\n💡 Cached for 3 hours to minimize API usage"
            return output

    class MCPSavePlanTool(BaseTool):
        """Save travel plans to persistent storage"""

        name: str = "save_travel_plan"
        description: str = """Save a travel plan to persistent storage.
        Plans are saved immediately and can be retrieved anytime."""
        args_schema: Type[BaseModel] = SavePlanInput

        def _run(self, plan_data: dict, plan_name: Optional[str] = None) -> str:
            return asyncio.run(self._arun(plan_data, plan_name))

        async def _arun(self, plan_data: dict, plan_name: Optional[str] = None) -> str:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                city = plan_data.get("city", "unknown")
                plan_id = f"{city}_{timestamp}"

                full_plan = {
                    "plan_id": plan_id,
                    "plan_name": plan_name or f"{city} Trip",
                    "created_at": datetime.now().isoformat(),
                    "data": plan_data
                }

                # File system MCP doesn't have rate limits, so no caching needed
                await mcp_manager.call_tool_with_cache(
                    "filesystem",
                    "write_file",
                    {
                        "path": f"{plan_id}.json",
                        "content": json.dumps(full_plan, indent=2)
                    },
                    bypass_cache=True  # Always write fresh
                )

                return (
                    f"✅ Travel plan saved successfully!\n"
                    f"📁 Plan ID: {plan_id}\n"
                    f"💾 Name: {full_plan['plan_name']}"
                )

            except Exception as e:
                logger.error(f"Save plan error: {e}")
                return f"❌ Failed to save: {str(e)}"

    class MCPLoadPlanTool(BaseTool):
        """Load saved travel plans"""

        name: str = "load_travel_plan"
        description: str = """Load a previously saved travel plan.
        Cached for 1 hour to minimize file system access."""
        args_schema: Type[BaseModel] = LoadPlanInput

        def _run(self, plan_id: str) -> str:
            return asyncio.run(self._arun(plan_id))

        async def _arun(self, plan_id: str) -> str:
            try:
                result = await mcp_manager.call_tool_with_cache(
                    "filesystem",
                    "read_file",
                    {"path": f"{plan_id}.json"},
                    cache_category="places"
                )

                if hasattr(result, 'content'):
                    for item in result.content:
                        if hasattr(item, 'text'):
                            plan_data = json.loads(item.text)
                            return (
                                f"✅ Loaded: {plan_data.get('plan_name')}\n\n"
                                f"{json.dumps(plan_data, indent=2)}"
                            )

                return str(result)

            except Exception as e:
                logger.error(f"Load plan error: {e}")
                return f"❌ Failed to load plan {plan_id}: {str(e)}"

    class MCPUserMemoryTool(BaseTool):
        """Store and retrieve user preferences"""

        name: str = "user_memory"
        description: str = """Store or retrieve user preferences.
        Cached for 1 hour. Use for personalization."""
        args_schema: Type[BaseModel] = UserMemoryInput

        def _run(self, user_id: str, key: str, value: Optional[str] = None) -> str:
            return asyncio.run(self._arun(user_id, key, value))

        async def _arun(self, user_id: str, key: str, value: Optional[str] = None) -> str:
            try:
                memory_key = f"{user_id}:{key}"

                if value is not None:
                    # Store
                    await mcp_manager.call_tool_with_cache(
                        "memory",
                        "store_memory",
                        {"key": memory_key, "value": value},
                        bypass_cache=True
                    )
                    return f"✅ Stored {key} for {user_id}"
                else:
                    # Retrieve (with cache)
                    result = await mcp_manager.call_tool_with_cache(
                        "memory",
                        "retrieve_memory",
                        {"key": memory_key},
                        cache_category="memory"
                    )

                    if hasattr(result, 'content'):
                        for item in result.content:
                            if hasattr(item, 'text'):
                                return f"📝 {user_id}.{key}: {item.text}"

                    return str(result)

            except Exception as e:
                logger.error(f"Memory error: {e}")
                return f"❌ Memory operation failed: {str(e)}"

    def get_mcp_tools() -> List[BaseTool]:
        """Get all MCP-powered LangChain tools"""
        return [
            MCPWeatherTool(),
            MCPSavePlanTool(),
            MCPLoadPlanTool(),
            MCPUserMemoryTool()
        ]

else:
    def get_mcp_tools():
        logger.warning("LangChain not available, returning empty tools list")
        return []


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_mcp_status() -> Dict:
    """Get status of all MCP servers and caching"""
    status = {
        "mcp_available": MCP_AVAILABLE,
        "servers": {},
        "cache_stats": cache_manager.get_cache_stats()
    }

    for server_name, server_info in mcp_manager.servers.items():
        status["servers"][server_name] = {
            "initialized": True,
            "tools": server_info["tools"],
            "initialized_at": server_info["initialized_at"],
            "rate_limit": cache_manager.get_rate_limit_status(server_name)
        }

    return status


async def test_mcp_integration():
    """Test MCP integration with caching"""
    print("\n" + "="*60)
    print("Testing MCP Integration with Caching")
    print("="*60 + "\n")

    # Initialize
    print("Initializing MCP servers...")
    results = await initialize_mcp_servers()
    print(f"Initialization results: {results}\n")

    if not any(results.values()):
        print("❌ No MCP servers initialized")
        return

    # Get status
    print("MCP Status:")
    status = get_mcp_status()
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    asyncio.run(test_mcp_integration())
