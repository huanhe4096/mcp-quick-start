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

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

otel_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
tracer_provider = TracerProvider(resource=Resource({"service.name": "autogen-test-agentchat"}))
span_processor = BatchSpanProcessor(otel_exporter)
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)

# we will get reference this tracer later using its service name
# tracer = trace.get_tracer("autogen-test-agentchat")


print("* loaded libs")


async def main():
    tracer = trace.get_tracer("autogen-test-agentchat")
    
    with tracer.start_as_current_span("research_analysis") as main_span:
        #%% define MCP servers
        with tracer.start_as_current_span("setup_mcp_servers"):
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
        with tracer.start_as_current_span("setup_agents"):
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
        # Example task
        task = """
        Please analyze the following research papers and provide a summary of their findings:
        1. PMID: 36990608
        2. PMID: 36990609

        Focus on:
        - Key findings and outcomes
        - Clinical implications
        """
        with tracer.start_as_current_span("analyze_research_papers") as span:
            span.set_attribute("task", task)
            await Console(team.run_stream(task=task))
            await model_client.close()

        # Run the analysis

if __name__ == "__main__":
    asyncio.run(main()) 