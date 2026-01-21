from fastapi import FastAPI
from fastmcp import FastMCP
from contextlib import asynccontextmanager
from typing import Dict, Any, Union, Optional

import subprocess

app = FastAPI()
mcp = FastMCP.from_fastapi(app=app, name="Nikto MCP")
mcp_app = mcp.http_app(path='/mcp')

@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    print("Starting Nikto FastAPI")
    async with mcp_app.lifespan(app):
        print("Starting Nikto FastMCP")
        yield
    print("Shutting down Nikto FastAPI and FastMCP")


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
        name="nikto_scan",
        description=(
            "Executes a REAL Nikto web vulnerability scan against a target web service. "
            "Use this tool for baseline web vulnerability discovery and misconfiguration checks. "
            "Results are live and must not be fabricated."
        )
)
async def nikto_scan(target: str, port: Union[str, int], additional_args: str = "") -> Dict[str, Any]:

        """
        Perform a Nikto scan on a target web service.

        Args:
            target (str):
                Hostname or IP address (e.g. juice-shop or 127.0.0.1)
            port (str, optional):
                Port number (e.g. 3000). If empty, Nikto default is used.
            ssl (bool, optional):
                Use SSL/TLS (-ssl). Defaults to False.
            additional_args (str, optional):
                Extra Nikto command-line arguments.

        Returns:
            dict:
                * content: Nikto stdout (truncated)
                * metadata: return code and stderr
        """

        cmd = ["nikto", "-host", target]

        if port:
            cmd.extend(["-p", str(port)])

        if additional_args:
            cmd.extend(additional_args.split())

        print(f"Nikto scan called for target: {target}\nCMD: {cmd}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180
            )

        except subprocess.TimeoutExpired:
            return {
                "error": "Nikto scan timed out",
                "target": target,
                "port": port
            }
        except Exception as e:
            return {
                "error": str(e),
                "target": target,
                "port": port
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
