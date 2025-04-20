#%% 
import nest_asyncio
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import StructuredMessage, TextMessage
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools


nest_asyncio.apply()
print('* applied nest_asyncio')

#%% define base llm
model_client = OpenAIChatCompletionClient(
    model="gpt-4.1-nano"
)
print('* defined the base llm')

agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
)
print('* defined the assistant agent')


#%% a very simple test
async def test_basic() -> None:
    print(await agent.run(task="Say 'Hello World!'"))
    await model_client.close()


#%% run the simple test
asyncio.run(test_basic())



#%% a more complex test
########################################################
async def assistant_run_stream() -> None:
    # Option 1: read each message from the stream (as shown in the previous example).
    # async for message in agent.on_messages_stream(
    #     [TextMessage(content="Find information on AutoGen", source="user")],
    #     cancellation_token=CancellationToken(),
    # ):
    #     print(message)

    # Option 2: use Console to print all messages as they appear.
    await Console(
        agent.on_messages_stream(
            [TextMessage(content="Find information on AutoGen and write a short summary of the information.", source="user")],
            cancellation_token=CancellationToken(),
        ),
        output_stats=True,  # Enable stats printing.
    )


#%% run the more complex test
# Use asyncio.run(assistant_run_stream()) when running in a script.
asyncio.run(assistant_run_stream())


#%%
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools

# Get the fetch tool from mcp-server-fetch.
fetch_mcp_server = StdioServerParams(command="uvx", args=["mcp-server-fetch"])
tools = await mcp_server_tools(fetch_mcp_server)

# Create an agent that can use the fetch tool.
model_client = OpenAIChatCompletionClient(model="gpt-4.1-nano")
agent = AssistantAgent(name="fetcher", model_client=model_client, tools=tools, reflect_on_tool_use=True)  # type: ignore

# Let the agent fetch the content of a URL and summarize it.
result = await agent.run(task="Summarize the content of https://en.wikipedia.org/wiki/Seattle")
assert isinstance(result.messages[-1], TextMessage)
print(result.messages[-1].content)

# Close the connection to the model client.
await model_client.close()
