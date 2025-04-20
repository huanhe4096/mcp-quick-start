#%% load libs
import os
from dotenv import load_dotenv
from smolagents import CodeAgent, OpenAIServerModel, tool
from phoenix.otel import register
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from smolagents import MCPClient

# Load environment variables
load_dotenv()

# Register and instrument for tracing
register()
SmolagentsInstrumentor().instrument()
print("* loaded libs and instrumented the agent")


#%% define the agents
# Extractor Agent
with MCPClient([
    { "url": "http://localhost:50001/sse" },
    { "url": "http://localhost:50002/sse" },
]) as tools:

    extractor_agent = CodeAgent(
        tools=tools,
        model=OpenAIServerModel(
            model_id="gpt-4.1-nano",
            api_key=os.getenv("OPENAI_API_KEY"),
        ),
        description="""
        You are an expert in extracting information from research papers and clinical trials.
        Your role is to:
        1. Extract key information from papers using the provided tools
        2. Identify relevant clinical trial IDs, study designs, and outcomes
        3. Organize the extracted information in a structured format
        4. Pass the extracted information to the summarizer agent
        
        When you have completed extracting information, end your message with "EXTRACTION_COMPLETE".
        """,
    )

    # Summarizer Agent
    summarizer_agent = CodeAgent(
        tools=[],
        model=OpenAIServerModel(
            model_id="gpt-4.1-nano",
            api_key=os.getenv("OPENAI_API_KEY"),
        ),
        description="""
        You are an expert in summarizing research findings and drawing conclusions.
        Your role is to:
        1. Review the extracted information from papers
        2. Identify key findings and patterns
        3. Draw meaningful conclusions
        4. Provide clear explanations of the findings
        5. Highlight any limitations or gaps in the research
        
        When you have completed the summary, end your message with "SUMMARY_COMPLETE".
        """,
    )

    print("* defined the agents")

#%% example usage
def analyze_research_papers(task: str):
    """
    Analyze research papers based on the given task.
    
    Args:
        task: A string describing what information to extract and analyze from the papers
    """
    # First, let the extractor agent gather information
    extraction_result = extractor_agent.run(task)
    print("\nExtraction Results:")
    print(extraction_result)
    
    # Then, let the summarizer agent analyze and summarize
    summary_result = summarizer_agent.run(extraction_result)
    print("\nSummary Results:")
    print(summary_result)

# Example task
task = """
Please analyze the following research papers and provide a summary of their findings:
1. PMID: 36990608
2. PMID: 36990609

Focus on:
- Study design and methodology
- Key findings and outcomes
- Clinical implications
- Any limitations or gaps in the research
"""

# Run the analysis
analyze_research_papers(task) 