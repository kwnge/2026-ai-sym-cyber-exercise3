from fastapi import FastAPI
from fastmcp import FastMCP
from contextlib import asynccontextmanager
from typing import Dict

import subprocess

app = FastAPI()
mcp = FastMCP.from_fastapi(app=app, name="curl MCP")
mcp_app = mcp.http_app(path='/mcp')

@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    print("Starting curl FastAPI")
    async with mcp_app.lifespan(app):
        print("Starting curl FastMCP")
        yield
    print("Shutting down curl FastAPI and FastMCP")


# Combined routes and app
combined_app = FastAPI(
    routes=[
        *mcp_app.routes,
        *app.routes,
    ],
    lifespan=combined_lifespan,
)


@app.get("/health")
async def api_health_check():
    """
    Docstring for health_check
    """
    return {
        "status": "ok",
        "message": "Server is healthy"
    }

@mcp.tool
async def mcp_health_check():
    return {
        "status": "ok",
        "message": "Server is healthy"
    }

@mcp.tool(
    name="curl",
    description=(
        "Executes a REAL curl request. "
        "Use this tool to download resources, inspect raw responses, or validate file exposure. "
        "Results are live and not simulated."
    )
)
async def curl_cmd(
    url: str,
    additional_args: str = ""
) -> Dict[str, any]:
    """
    Docstring for curl_cmd
    
    :return: Description
    :rtype: Dict[str, Any]
    """

    cmd = ["curl", "-L"]
    if additional_args:
        cmd.extend(additional_args.split())

    cmd.extend(url)

    print(f"curl command called for for url: {url}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

    except subprocess.TimeoutExpired:
        return {
            "error": "curl request timed out",
            "url": url
        }
    except Exception as e:
        return {
            "error": str(e),
            "url": url
        }

    return {
        "content": [
            {
                "type": "text",
                "text": result.stdout[:8000]
            }
        ],
        "metadata": {
            "returncode": result.returncode,
            "stderr": result.stderr[:2000]
        }
    }