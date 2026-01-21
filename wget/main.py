from fastapi import FastAPI
from fastmcp import FastMCP
from contextlib import asynccontextmanager
from typing import Dict, Any, Union, Optional

import subprocess

app = FastAPI()
mcp = FastMCP.from_fastapi(app=app, name="Wget MCP")
mcp_app = mcp.http_app(path='/mcp')

@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    print("Starting Wget FastAPI")
    async with mcp_app.lifespan(app):
        print("Starting Wget FastMCP")
        yield
    print("Shutting down Wget FastAPI and FastMCP")


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
    name="wget_fetch",
    description=(
        "Executes a REAL wget request to retrieve web content or files from a target URL. "
        "Use this tool to download resources, inspect raw responses, or validate file exposure. "
        "Results are live and not simulated."
    )
)
async def wget_fetch(
    url: str,
    headers: Optional[str] = "",
    additional_args: str = ""
) -> Dict[str, Any]:
    """
    Fetch content using wget.

    Args:
        url (str):
            Full URL to retrieve.
        headers (str, optional):
            Custom headers as a single string, e.g. 'Authorization: Bearer <token>'.
        additional_args (str, optional):
            Extra wget arguments (e.g. '--server-response', '--no-check-certificate').

    Returns:
        dict:
            * content: wget stdout (truncated)
            * metadata: return code and stderr
    """

    cmd = ["wget", "-qO-"]

    if headers:
        cmd.extend(["--header", headers])

    if additional_args:
        cmd.extend(additional_args.split())

    cmd.append(url)

    print(f"wget_fetch called for url: {url}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

    except subprocess.TimeoutExpired:
        return {
            "error": "wget request timed out",
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
