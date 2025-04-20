#%% load libs
import os
from dotenv import load_dotenv
from smolagents import CodeAgent, ToolCallingAgent, OpenAIServerModel, tool
from phoenix.otel import register
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from smolagents.mcp_client import MCPClient

# Load environment variables
load_dotenv()

# Register and instrument for tracing
register()
SmolagentsInstrumentor().instrument()
print("* loaded libs and instrumented the agent")


#%% define the agents
# Extractor Agent
mcp_client = MCPClient([
    { "url": "http://localhost:50001/sse" },
    { "url": "http://localhost:50002/sse" },
])
tools = mcp_client.get_tools()

extractor_agent = ToolCallingAgent(
    tools=tools,
    model=OpenAIServerModel(
        # model_id="gpt-4.1-nano",
        model_id="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
    ),
    name="extractor_agent",
    description="""You are an expert in extracting information from research papers.""",
    max_steps=3,
)

# Manager Agent
manager_agent = CodeAgent(
    tools=[],
    model=OpenAIServerModel(
        model_id="gpt-4.1-nano",
        api_key=os.getenv("OPENAI_API_KEY"),
    ),
    managed_agents=[extractor_agent],
    name="manager_agent",
    description="""
    You are an expert in summarizing research findings and drawing conclusions.""",
)

print("* defined the agents")

#%% example task
task = """
Please analyze the following research papers and provide a summary of their findings:
1. PMID: 36990608
2. PMID: 36990609
"""

# Run the analysis
summary_result = manager_agent.run(task)
print("\nSummary Results:")
print(summary_result)