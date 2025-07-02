from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from tools import tools
from config import config
import os

# Initialize the LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=config.GOOGLE_API_KEY,
    temperature=0.3,
    max_tokens=1000  # Limit response length
)

# Optimized prompt template for faster responses
prompt_template = PromptTemplate(
    input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
    template="""You are a travel planning assistant. Generate a concise plan quickly.

Available tools: {tool_names}
{tools}

User request: {input}

Instructions:
1. Use 1-2 tools maximum to get place and restaurant data
2. Recommend exactly 1 place to visit and 1 place to eat
3. Keep responses short and focused
4. Format as: VISIT: [place] | EAT: [restaurant] | WHY: [brief reason]

{agent_scratchpad}

Response:"""
)

# Create agent with timeout settings
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt_template
)

# Configure agent executor with strict limits
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=3,  # Reduced from default
    max_execution_time=30,  # 30 second timeout
    early_stopping_method="generate",
    handle_parsing_errors=True
)