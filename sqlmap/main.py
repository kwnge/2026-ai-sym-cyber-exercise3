from fastapi import FastAPI
from fastmcp import FastMCP
import asyncio
from uuid import uuid4
from contextlib import asynccontextmanager
from typing import Dict, Any

import subprocess

app = FastAPI()
mcp = FastMCP.from_fastapi(app=app, name="sqlmap MCP")
mcp_app = mcp.http_app(path='/mcp')

@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    print("Starting sqlmap FastAPI")
    async with mcp_app.lifespan(app):
        print("Starting sqlmap FastMCP")
        yield
    print("Shutting down sqlmap FastAPI and FastMCP")


# Combined routes and app
combined_app = FastAPI(
    routes=[
        *mcp_app.routes,
        *app.routes,
    ],
    lifespan=combined_lifespan,
)

# Shared state globals
job_results: Dict[str, Any] = {}
job_state: Dict[str, str] = {}


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


#@mcp.tool(
#    name="sqlmap_scan",
#    description=(
#        "Executes a REAL sqlmap scan against a target URL or request file. "
#        "Use this tool to identify SQL injection vulnerabilities and enumerate "
#        "databases. Results are live and not simulated."
#    )
#)
#async def sqlmap_scan(
#    target: str,
#    level: int = 1,
#    risk: int = 1,
#    method: str = "GET",
#    data: str = "",
#    cookie: str = "",
#    additional_args: str = ""
#) -> Dict[str, Any]:
#    """
#    Run sqlmap against a target.
#
#    Args:
#        target (str):
#            Target URL (e.g. http://host/item?id=1) or request file (-r file).
#        level (int):
#            Test level (1–5).
#        risk (int):
#            Risk level (1–3).
#        method (str, optional):
#            HTTP method (GET, POST, PUT).
#        data (str, optional):
#            POST data string.
#        cookie (str, optional):
#            Cookie header.
#        additional_args (str, optional):
#            Extra sqlmap flags (e.g. '--dbs', '--tables').
#
#    Returns:
#        dict:
#            content: sqlmap stdout (truncated)
#            metadata: return code and stderr
#    """
#
#    cmd = [
#        "sqlmap",
#        "-u", target,
#        "--batch",
#        f"--level={level}",
#        f"--risk={risk}",
#    ]
#
#    if method:
#        cmd.extend(["--method", method])
#
#    if data:
#        cmd.extend(["--data", data])
#
#    if cookie:
#        cmd.extend(["--cookie", cookie])
#
#    if additional_args:
#        cmd.extend(additional_args.split())
#
#    print(f"sqlmap_scan called for target: {target}")
#
#    try:
#        result = subprocess.run(
#            cmd,
#            capture_output=True,
#            text=True,
#            timeout=600
#        )
#
#    except subprocess.TimeoutExpired:
#        return {
#            "error": "sqlmap scan timed out",
#            "target": target
#        }
#    except Exception as e:
#        return {
#            "error": str(e),
#            "target": target
#        }
#
#    return {
#        "content": [
#            {
#                "type": "text",
#                "text": result.stdout[:8000]
#            }
#        ],
#        "metadata": {
#            "returncode": result.returncode,
#            "stderr": result.stderr[:2000]
#        }
#    }
#

async def run_sqlmap_scan(job_id: str, cmd: list[str]):
    job_state[job_id] = "running"
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=600
        )

        job_results[job_id] = {
            "stdout": result.stdout[:8000],
            "stderr": result.stderr[:2000],
            "returncode": result.returncode,
        }
        job_state[job_id] = "completed"

    except asyncio.TimeoutError:
        job_state[job_id] = "failed"
        job_results[job_id] = {
            "error": "sqlmap timed out",
            "cmd": cmd
        }

    except Exception as e:
        job_state[job_id] = "failed"
        job_results[job_id] = {
            "error": str(e),
            "cmd": cmd
        }

@mcp.tool(
    name="start_sqlmap_scan",
    description=(
        "Executes a REAL sqlmap scan against a target URL or request file. "
        "Use this tool to identify SQL injection vulnerabilities and enumerate "
        "databases. Results are live and not simulated."
        "A job id is returned. Use this job id to check the status of your sqlmap scan."
    )
)
async def start_sqlmap_scan(
    target: str,
    level: int = 1,
    risk: int = 1,
    method: str = "GET",
    data: str = "",
    cookie: str = "",
    additional_args: str = ""
) -> Dict[str, Any]:
    """
    Run sqlmap against a target.

    Args:
        target (str):
            Target URL (e.g. http://host/item?id=1) or request file (-r file).
        level (int):
            Test level (1–5).
        risk (int):
            Risk level (1–3).
        method (str, optional):
            HTTP method (GET, POST, PUT).
        data (str, optional):
            POST data string.
        cookie (str, optional):
            Cookie header.
        additional_args (str, optional):
            Extra sqlmap flags (e.g. '--dbs', '--tables').

    Returns:
        dict:
            content: sqlmap stdout (truncated)
            metadata: return code and stderr
    """
    job_id = uuid4().hex
    cmd = [
        "sqlmap",
        "-u", target,
        "--batch",
        f"--level={level}",
        f"--risk={risk}",
    ]

    if method:
        cmd.extend(["--method", method])

    if data:
        cmd.extend(["--data", data])

    if cookie:
        cmd.extend(["--cookie", cookie])

    if additional_args:
        cmd.extend(additional_args.split())

    print(f"sqlmap_scan called for target: {target}")
    print(f"sqlmap command being run: \n{cmd}")

    try:
        asyncio.create_task(run_sqlmap_scan(job_id=job_id, cmd=cmd))
    except Exception as e:
        return {
            "error": str(e),
            "target": target
        }
    
    return {"job_id": job_id}

@mcp.tool(
    name="get_sqlmap_status",
    description="Returns the current status and results (if available) for a sqlmap scan job."
    "If status is running, wait before checking again."
)
async def get_sqlmap_status(job_id: str) -> Dict[str, Any]:
    if job_id not in job_state:
        return {
            "status": "unknown",
            "error": "job_id not found"
        }

    response: Dict[str, Any] = {
        "job_id": job_id,
        "status": job_state[job_id],
    }

    if job_state[job_id] == "running":
        response["message"] = "sqlmap scan is still running"
        response["next_action"] = "wait"
        response["retry_after_seconds"] = 30

    if job_state[job_id] == "completed":
        response["result"] = job_results.get(job_id)

    if job_state[job_id] == "failed":
        response["error"] = job_results.get(job_id)

    return response

@mcp.tool(
    name="sqlmap_wait",
    description="Use this tool to wait a specified amount of time for sqlmap tool to finish."
)
async def wait_sqlmap_status(job_id: str, wait_time: float = 30):
    await asyncio.sleep(wait_time)

    # TODO Add returning job status after wait
    return {
        "job_id": job_id,
        "waited_time": wait_time
    }