import asyncio
from contextlib import AsyncExitStack
from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings


async def main():
    
    trace_id = gen_trace_id()
    with trace(workflow_name="IE+MCPs Demo", trace_id=trace_id):
        print(f"* View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
                
        # define MCP servers
        async with AsyncExitStack() as stack:
            # define MCP servers
            
            # the PubMed MCP server
            mcp_pubmed = await stack.enter_async_context(
                MCPServerSse(
                    name="MCP/PubMed",
                    params={
                        "url": "http://localhost:50002/sse",
                    },
                )
            )
            
            # the Clinical Trial MCP server
            mcp_clinical_trial = await stack.enter_async_context(
                MCPServerSse(
                    name="MCP/Clinical_Trial",
                    params={
                        "url": "http://localhost:50001/sse",
                    },
                )
            )
            
            # define a single agent for this task
            agent = Agent(
                name="Extraction Assistant",
                instructions="You are a clinical trial expert. Use the tools if necessary to answer the questions.",
                mcp_servers=[
                    mcp_pubmed,
                    mcp_clinical_trial
                ],
                model="gpt-4o-mini",
                model_settings=ModelSettings(
                    tool_choice="required",
                    temperature=0.1,
                ),
            )

            # Example 1: Get the trial ID from a paper, but only provide the PMID
            message = "What is the NCT ID for the paper PMID: 36990608?"
            print(f"- User:\n{message}\n")
            result = await Runner.run(starting_agent=agent, input=message)
            print(f"$ Assistant:\n{result.final_output}\n")
        


if __name__ == "__main__":
    asyncio.run(main())