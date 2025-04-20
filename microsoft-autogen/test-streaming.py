from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
import asyncio

# Create an agent that can use the fetch tool.
model_client = OpenAIChatCompletionClient(model="gpt-4.1-nano")
agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    reflect_on_tool_use=True,
    system_message="You are a helpful assistant.",
    model_client_stream=True,  # Enable streaming tokens.
)  # type: ignore

async def run():
    async for message in agent.on_messages_stream(  # type: ignore
        [TextMessage(content="Name two cities in South America", source="user")],
        cancellation_token=CancellationToken(),
    ):
        print(message)

if __name__ == "__main__":
    asyncio.run(run())