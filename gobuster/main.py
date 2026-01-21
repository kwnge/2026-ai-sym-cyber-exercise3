from fastapi import FastAPI
from fastmcp import FastMCP
from contextlib import asynccontextmanager
from typing import Dict, Any

import os
import subprocess

app = FastAPI()
mcp = FastMCP.from_fastapi(app=app, name="gobuster MCP")
mcp_app = mcp.http_app(path='/mcp')

@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    print("Starting gobuster FastAPI")
    async with mcp_app.lifespan(app):
        print("Starting gobuster FastMCP")
        yield
    print("Shutting down gobuster FastAPI and FastMCP")


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
    name="gobuster_dir",
    description=(
        "Executes a REAL Gobuster directory brute-force scan against a web target. "
        "Use this tool to discover hidden paths, files, and endpoints. "
        "Results are live and not simulated. "
        "Common wordlists: /usr/share/wordlists/dirb/common.txt, "
        "/usr/share/seclists/Discovery/Web-Content/common.txt"
    )
)
async def gobuster_dir(
    url: str,
    wordlist: str,
    extensions: str = "",
    additional_args: str = ""
) -> Dict[str, Any]:
    """
    Run Gobuster directory scan.
    Args:
        url (str): Target URL (e.g. http://juice-shop:3000)
        wordlist (str): Path to wordlist
        extensions (str): File extensions (e.g. php,txt,js)
        additional_args (str): Extra gobuster flags (e.g. "-t 50 --no-error")
    Returns:
        dict: Consistent structure with content array and isError flag
    """
    
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        return {
            "content": [{
                "type": "text",
                "text": f"Error: URL must start with http:// or https://. Got: {url}"
            }],
            "isError": True
        }
    
    # Validate wordlist exists
    if not os.path.isfile(wordlist):
        return {
            "content": [{
                "type": "text",
                "text": f"Error: Wordlist not found at path: {wordlist}\n"
                        f"Common locations:\n"
                        f"  - /usr/share/wordlists/dirb/common.txt\n"
                        f"  - /usr/share/seclists/Discovery/Web-Content/common.txt"
            }],
            "isError": True
        }
    
    # Build command
    cmd = [
        "gobuster", "dir",
        "-u", url,
        "-w", wordlist,
    ]
    
    if extensions:
        cmd.extend(["-x", extensions])
    
    if additional_args:
        cmd.extend(additional_args.split())
    
    print(f"Gobuster dir scan called for url: {url}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Check if gobuster itself failed
        if result.returncode != 0:
            error_msg = f"Gobuster failed with return code {result.returncode}\n\n"
            if result.stderr:
                error_msg += f"Error output:\n{result.stderr[:2000]}\n\n"
            if result.stdout:
                error_msg += f"Standard output:\n{result.stdout[:2000]}"
            
            return {
                "content": [{
                    "type": "text",
                    "text": error_msg
                }],
                "isError": True
            }
        
        # Success case
        output = result.stdout if result.stdout else "Scan completed but no output generated"
        
        return {
            "content": [{
                "type": "text",
                "text": output[:8000]  # Truncate to reasonable size
            }],
            "isError": False
        }
        
    except subprocess.TimeoutExpired:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: Gobuster scan timed out after 300 seconds for URL: {url}\n"
                        f"Try using fewer threads or a smaller wordlist."
            }],
            "isError": True
        }
    
    except FileNotFoundError:
        return {
            "content": [{
                "type": "text",
                "text": "Error: 'gobuster' command not found. Is it installed?\n"
                        f"Install with: apt-get install gobuster  or  brew install gobuster"
            }],
            "isError": True
        }
    
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error running gobuster: {str(e)}\n"
                        f"URL: {url}\n"
                        f"Wordlist: {wordlist}"
            }],
            "isError": True
        }
