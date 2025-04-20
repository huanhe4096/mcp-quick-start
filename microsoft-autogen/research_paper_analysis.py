#%% load libs
import asyncio
import nest_asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import SseServerParams, mcp_server_tools

nest_asyncio.apply()
print("* loaded libs")

async def main():
    #%% define MCP servers
    # Clinical Trial MCP server
    clinical_trial_mcp = SseServerParams(
        url="http://localhost:50001/sse"
    )

    # PubMed MCP server
    pubmed_mcp = SseServerParams(
        url="http://localhost:50002/sse"
    )

    # Get tools from MCP servers
    clinical_trial_tools = await mcp_server_tools(clinical_trial_mcp)
    pubmed_tools = await mcp_server_tools(pubmed_mcp)

    #%% define the agents
    model_client = OpenAIChatCompletionClient(model="gpt-4.1-nano")

    # Extractor Agent - Specialized in extracting information from papers
    extractor_agent = AssistantAgent(
        name="extractor",
        model_client=model_client,
        tools=clinical_trial_tools + pubmed_tools,
        system_message="""
        You are an expert in extracting information from research papers and clinical trials.
        Your role is to:
        1. Extract key information from papers using the provided tools
        2. Identify relevant clinical trial IDs, study designs, and outcomes
        3. Organize the extracted information in a structured format
        4. Pass the extracted information to the summarizer agent
        
        When you have completed extracting information, end your message with "EXTRACTION_COMPLETE".
        """,
    )

    # Summarizer Agent - Specialized in summarizing and drawing conclusions
    summarizer_agent = AssistantAgent(
        name="summarizer",
        model_client=model_client,
        system_message="""
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

    # Define termination conditions
    extraction_termination = TextMentionTermination("EXTRACTION_COMPLETE")
    summary_termination = TextMentionTermination("SUMMARY_COMPLETE")
    termination = extraction_termination | summary_termination

    # Create the team
    team = RoundRobinGroupChat(
        [extractor_agent, summarizer_agent],
        termination_condition=termination,
    )

    #%% example usage
    async def analyze_research_papers(task: str):
        """
        Analyze research papers based on the given task.
        
        Args:
            task: A string describing what information to extract and analyze from the papers
        """
        await Console(team.run_stream(task=task))
        await model_client.close()

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
    await analyze_research_papers(task)

if __name__ == "__main__":
    asyncio.run(main()) 