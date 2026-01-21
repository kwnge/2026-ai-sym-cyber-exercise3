from fastapi import FastAPI
from fastmcp import FastMCP
from contextlib import asynccontextmanager
from typing import Dict, Any, Union

import subprocess

app = FastAPI()
mcp = FastMCP.from_fastapi(app=app, name="nmap MCP")
mcp_app = mcp.http_app(path='/mcp')

@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    print("Starting nmap FastAPI")
    async with mcp_app.lifespan(app):
        print("Starting nmap FastMCP")
        yield
    print("Shutting down nmap FastAPI and FastMCP")


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
    name="nmap_scan",
    description=(
        "Executes a REAL nmap scan on the host system and returns live results. "
        "Use this tool whenever port or service discovery is required. "
        "Do NOT guess or fabricate ports — results must come from this tool."
    )
)
async def nmap_scan(target: str, scan_type: str = "-sV", ports: Union[str, int] = "", additional_args: str = "") -> Dict[str, Any]:
    """
    Perform an nmap scan on a target host and return the live results.

    Args:
        target (str):
            The hostname or IP address to scan.
        scan_type (str, optional):
            Nmap scan type (e.g. ``-sS`` for SYN scan, ``-sV`` for version detection,
            ``-Pn`` to skip host discovery, etc.).  Defaults to ``"-sV"``.
        ports (str, optional):
            Comma‑separated list of ports to scan.  If empty, nmap will scan the
            default set of ports.  Defaults to ``""`` (scan all ports).
        additional_args (str, optional):
            Any extra command‑line arguments you want to pass directly to nmap.
            Defaults to ``""``.

    Returns:
        dict:
            * On success – a dictionary with two keys:
                - ``content``: a list containing a single ``text`` block that holds
                  the scan output (stdout) truncated to 8000 characters.
                - ``metadata``: a dictionary containing:
                    - ``returncode``: the process exit code,
                    - ``stderr``: the standard‑error output (up to 2000 characters).
            * On failure – a dictionary with an ``error`` key describing the problem
              (e.g., timeout, exception) and the original parameters for context.

    Raises:
        This function does **not** raise exceptions; any errors are caught internally
        and returned as part of the result dictionary.

    Example:
        >>> result = nmap_scan(
        ...     target="example.com",
        ...     scan_type="-sV",
        ...     ports="80,443",
        ...     additional_args="--script vuln"
        ... )
        >>> print(result["content"][0]["text"][:200])   # preview of stdout
        >>> print(result["metadata"]["returncode"])    # exit status
    """

    
    cmd = ["nmap", scan_type, "-p", str(ports), target] + additional_args.split()
    print(f"Nmap scan called for target: {target}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=90
        )

    except subprocess.TimeoutExpired:
        return {
            "error": "Nmap scan timed out",
            "target": target,
            "scan_type": scan_type,
            "ports": ports
        }
    except Exception as e:
        return {
            "error": str(e),
            "target": target,
            "scan_type": scan_type,
            "ports": ports
        }
    
    print(f"returning stdout: {result.stdout}")
    print(f"returning stderr: {result.stderr}")
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