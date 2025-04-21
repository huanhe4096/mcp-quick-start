# MCP Quickstart

```bash
uv venv --python 3.11
source .venv/bin/activate
uv sync
```

I want to take a look a different frameworks. The following points need to be considered:

1. Documentation: having comprehensive documents is very important for development
2. Community support: the more people use, the better support
3. Main contributor: person-driven, community-driven, or company-driven
4. Showcase: big projects

## OpenAI's Agent SDK

In the `/openai-agent-sdk`,

Pros:

- Simplicity
- Great integration with OpenAI's platform for tracking cost

Cons:

- It seems cost a lot.


## Huggingface's smolagents

Pros:

- Python code serves as the "language" for models.
- Very good integration with other tools
- The recommended tracing tool `phoenix` looks very good!

Cons:

- Bad documentation

## Microsoft's AutoGen

Pros:

- Documentation comprensive
- Provide support