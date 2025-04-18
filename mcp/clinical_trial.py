import re
import logging
import requests
from mcp.server.fastmcp import FastMCP

# Create server
mcp = FastMCP("Clinical Trial")


@mcp.tool()
def extract_nct_id(text: str) -> str:
    """Extract the clinical trial NCT ID from a given text"""
    logging.info(f"extract_nct_id from ({text})")
    return re.search(r"NCT\d+", text).group(0)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("action", type=str, choices=["run", "test"])
    parser.add_argument("--port", type=int, default=50001)
    args = parser.parse_args()

    if args.action == "run":
        mcp.settings.port = args.port
        mcp.run(
            transport="sse",
        )
    elif args.action == "test":
        print(extract_nct_id("This study is registered with ClinicalTrials.gov, NCT02446405, ANZCTR, ACTRN12614000110684, and EudraCT, 2014-003190-42."))

