import os
from config import config

# Handle imports with fallbacks
try:
    import google.generativeai as genai
    from langchain_google_genai import ChatGoogleGenerativeAI
    GENAI_AVAILABLE = True
except ImportError:
    print("Warning: google.generativeai not available. Install with: pip install google-generativeai")
    GENAI_AVAILABLE = False

try:
    from langchain.agents import create_openai_tools_agent, AgentExecutor
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    LANGCHAIN_AVAILABLE = True
except ImportError:
    print("Warning: LangChain agents not available")
    LANGCHAIN_AVAILABLE = False

from tools import tools

# Import MCP tools (optional)
try:
    from mcp_integration import get_mcp_tools
    mcp_tools = get_mcp_tools()
    print(f"✅ Loaded {len(mcp_tools)} MCP tools")
except ImportError as e:
    print(f"ℹ️ MCP tools not available: {e}")
    mcp_tools = []

# Configure Gemini
GOOGLE_API_KEY = config.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")

if GENAI_AVAILABLE and GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Initialize Gemini 1.5 Flash model (newer and more stable)
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",  # Updated to 1.5 Flash
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3,
            convert_system_message_to_human=True,
            max_retries=3,
            request_timeout=30
        )
        print("✅ Using Gemini 1.5 Flash model")
    except Exception as e:
        print(f"⚠️ Gemini 1.5 Flash failed, trying Gemini 1.5 Pro: {e}")
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",  # Fallback to 1.5 Pro
                google_api_key=GOOGLE_API_KEY,
                temperature=0.3,
                convert_system_message_to_human=True,
                max_retries=3,
                request_timeout=30
            )
            print("✅ Using Gemini 1.5 Pro model")
        except Exception as e2:
            print(f"❌ Both Gemini 1.5 models failed: {e2}")
            # Final fallback to basic model
            llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=GOOGLE_API_KEY,
                temperature=0.3,
                convert_system_message_to_human=True
            )
            print("⚠️ Using legacy Gemini Pro model")
else:
    print("Warning: Using fallback LLM - Gemini not configured")
    # Fallback LLM class
    class FallbackLLM:
        def invoke(self, messages):
            return {"content": "Fallback response - please configure Google API key"}
    
    llm = FallbackLLM()

# Create enhanced prompt for travel planning
if LANGCHAIN_AVAILABLE:
    travel_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert AI travel planner for India. Your goal is to create detailed, comprehensive itineraries using ONLY AI-generated real data from tools.

MCP-POWERED CAPABILITIES (All cached to minimize API costs):
🌤️ check_weather - Get real-time weather forecasts (cached 3hrs)
💾 save_travel_plan - Save plans for users to access later
📂 load_travel_plan - Load previously saved plans
🧠 user_memory - Remember user preferences across sessions
🗺️ calculate_route - Get directions and travel times between locations (cached 6hrs)
🔍 search_web - Search for current events, reviews, local tips (cached 8hrs)

CRITICAL REQUIREMENTS:
1. You MUST call tools to get AI-generated realistic data - NEVER use placeholder text
2. ALWAYS start with check_weather to get forecast and adapt recommendations to weather
3. ALWAYS call restaurant_search tool to get specific restaurant names with complete details
4. ALWAYS call google_places_search tool to get specific place names with full information
5. Call get_reviews tool for additional travel insights and tips
6. Use calculate_route between major attractions to provide travel times and directions
7. Use search_web to find current events, festivals, or recent reviews for the destination
8. If a tool returns insufficient results, try different search terms and call tools again
9. Only recommend places with 4.0+ ratings from tool results
10. Include ALL details from tool responses (ratings, prices, addresses, timings, why famous)
11. Consider weather when suggesting activities (indoor for hot/rainy, outdoor for pleasant)
12. Add route information (time, distance, mode) between consecutive locations in itinerary

ENHANCED TOOL USAGE STRATEGY:
- For EACH attraction: Call google_places_search with specific queries (e.g., "historical monuments", "temples", "parks")
- For EACH meal: Call restaurant_search with cuisine type and meal timing (e.g., "vegetarian lunch", "street food")
- For comprehensive planning: Call get_reviews for additional insights about the destination
- Use exact names, ratings, and details returned by tools
- Make multiple tool calls to gather comprehensive information

🕒 TIME-OF-DAY REQUIREMENT:
- For each day, you MUST recommend places for different times of day:
  • Morning (e.g., 8:00 AM - 12:00 PM): Outdoor or cool-weather attractions
  • Afternoon (e.g., 12:00 PM - 5:00 PM): Indoor, shaded, or museum-type attractions
  • Evening (e.g., 5:00 PM onwards): Popular evening spots, markets, or scenic locations
- For each time slot, call google_places_search with an appropriate time_of_day parameter and explain why the place fits that slot.

RESPONSE FORMAT REQUIREMENTS:
- Every place/restaurant name must be specific and real (from AI-generated tool results)
- Include complete address from tools
- Show exact ratings (e.g., "Rating: 4.5") from tools  
- Include opening hours, entry fees, duration from tools
- Add "Why Famous" information from tools
- Include specific restaurant details: cuisine, famous dishes, price ranges
- Format with proper headers, bullet points, and clear sections

ENHANCED OUTPUT FORMAT:
🏛️ DAY X: [City] Exploration - [Theme]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ [Time] - VISIT: [Exact Place Name from AI tool] (⭐ Rating: X.X)
📍 Address: [Complete address from tool]
🕒 Hours: [Opening hours from tool]  
💰 Entry: [Entry fee from tool]
⏱️ Duration: [Recommended duration from tool]
✨ Why Visit: [Why famous description from tool]

🍽️ [MEAL TIME]: [Exact Restaurant Name from AI tool] (⭐ Rating: X.X)
📍 Address: [Complete address from tool]
💰 Price: [Price range from tool]
🍛 Cuisine: [Cuisine type from tool]
⭐ Famous For: [Famous dishes from tool]
🍴 Specialties: [Specific dishes from tool]

📝 TRAVEL INSIGHTS: [Insights from get_reviews tool]

VALIDATION CHECKLIST:
✅ Every place/restaurant name is specific and from AI tools
✅ All ratings are from actual tool responses
✅ All addresses are complete from tools
✅ All prices/fees are from tool data
✅ No generic or placeholder text used
✅ Multiple tool calls made for comprehensive information
✅ Travel insights included from reviews tool

Remember: Call tools extensively and use their AI-generated realistic data. Never assume or use generic information.
You MUST provide recommendations for morning, afternoon, and evening time slots each day, using the time_of_day parameter in your tool calls.
"""),
        
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Combine regular tools with MCP tools
    all_tools = tools + mcp_tools
    print(f"📦 Total tools available: {len(all_tools)} ({len(tools)} regular + {len(mcp_tools)} MCP)")

    # Create agent with all tools
    if GENAI_AVAILABLE and GOOGLE_API_KEY:
        agent = create_openai_tools_agent(llm, all_tools, travel_prompt)

        # Create agent executor with enhanced configuration for AI-generated content
        agent_executor = AgentExecutor(
            agent=agent,
            tools=all_tools,
            verbose=True,
            max_iterations=20,  # Increased for more comprehensive AI generation
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            max_execution_time=180  # 3 minute timeout for AI generation
        )
    else:
        # Fallback agent executor
        class FallbackAgentExecutor:
            def invoke(self, input_dict):
                query = input_dict.get("input", "")
                return {
                    "output": f"Fallback response for: {query}. Please configure API keys.",
                    "intermediate_steps": []
                }
        
        agent_executor = FallbackAgentExecutor()