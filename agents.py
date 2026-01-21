from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.mcp import MCPServerStreamableHTTP
from local_models import LocalModels

from typing import List

from deps import Deps, AttackVector, ExploitResults

NIKTO_MCP = MCPServerStreamableHTTP('http://localhost:8005/mcp', max_retries=5, tool_prefix="nikto_prim")
NIKTO_MCP_SEC = MCPServerStreamableHTTP('http://localhost:8015/mcp', max_retries=5, tool_prefix="nikto_sec")
NMAP_MCP = MCPServerStreamableHTTP('http://localhost:8006/mcp', max_retries=5, tool_prefix="nmap")
CURL_MCP = MCPServerStreamableHTTP('http://localhost:8003/mcp', max_retries=5, tool_prefix="curl")
SQLMAP_MCP = MCPServerStreamableHTTP('http://localhost:8002/mcp', max_retries=5, tool_prefix="sqlmap")
SQLMAP_MCP_SEC = MCPServerStreamableHTTP('http://localhost:8012/mcp', max_retries=5, tool_prefix="sqlmap_sec")
WGET_MCP = MCPServerStreamableHTTP('http://localhost:8004/mcp', max_retries=5, tool_prefix="wget")
GOBUSTER_MCP = MCPServerStreamableHTTP('http://localhost:8001/mcp', max_retries=5, tool_prefix="gobuster")

#MCP_TOOL_SERVER_SEC = MCPServerStreamableHTTP('http://localhost:8001/mcp', max_retries=5)

mission_agent = Agent[Deps](
    model='anthropic:claude-sonnet-4-5',
    deps_type=Deps,
    instructions=(
        'You are a senior offensive cyber manager focused on running an effective, '
        'concise, accurate, and agile red team.'

        'Scope:\n'
        ' - Focus should be the quickest path to compromise for the engagement goal'
        ' - Engage with your tools as required to meet the engagenemt goal'
    )
)

gpt_52 = OpenAIChatModel(
    model_name='gpt-5.2',
    settings=OpenAIChatModelSettings(
        timeout=600
    )
)
opus_45 = AnthropicModel(
    model_name='claude-opus-4-5',
    settings=AnthropicModelSettings(
        timeout=600,
    )
)

# Recon specific to routes and public endpoints
recon_endpoint_agent = Agent[Deps](
    model=gpt_52,
    output_type=List[AttackVector],
    toolsets=[NIKTO_MCP],
    instructions=(
        "You are a senior application security recon specialist focused exclusively on "
        "identifying public endpoints in web applications.\n\n"

        "Output requirements:\n"
        "- Return a list of Attack Vector objects only.\n"
        "- Each Attack Vector MUST include:\n"
        "  • type: a concise identifier (e.g., 'SQLi – Boolean-based', Information Disclosure, Misconfiguration, Exposed Credentials).\n"
        "  • explicit_path: the full URL and parameter tested.\n"
        "  • payload: the exact payload used and the observed behavior.\n"
        "  • confirmed: true ONLY if exploitation was demonstrated.\n\n"

        "Rules:\n"
        "- Do NOT include remediation.\n"
        "- Do NOT include generic advice or explanations.\n"
    )
)

# Recon specific to SQLi
recon_sqli_agent = Agent[Deps](
    model=gpt_52,
    output_type=List[AttackVector],
    toolsets=[NIKTO_MCP_SEC, SQLMAP_MCP, WGET_MCP, CURL_MCP],
    instructions=(
        "You are a senior application security recon specialist focused exclusively on "
        "identifying SQL injection vulnerabilities in web applications.\n\n"

        "Scope:\n"
        "- Only assess inputs that interact with server-side databases.\n"
        "- Prioritize unauthenticated and low-privilege attack paths.\n"
        "- Use evidence-driven reasoning; do not speculate.\n\n"

        "Output requirements:\n"
        "- Return a list of Vulnerability objects only.\n"
        "- Each Vulnerability MUST include:\n"
        "  • type: a concise identifier (e.g., 'SQLi – Boolean-based', 'SQLi – Error-based').\n"
        "  • explicit_path: the full URL and parameter tested.\n"
        "  • payload: the exact payload used and the observed behavior.\n"
        "  • confirmed: true ONLY if exploitation was demonstrated.\n\n"

        "Rules:\n"
        "- Do NOT include remediation.\n"
        "- Do NOT include generic advice or explanations.\n"
        "- If no SQL injection is found, return an empty list.\n"
        "- Prefer minimal payloads that reliably prove impact.\n"
    )
)

# Breach/exploit specific to vulns identified in MissionKnowledge schema
exploit_agent = Agent[Deps](
    model=opus_45,
    output_type=ExploitResults,
    retries=3,
    toolsets=[SQLMAP_MCP, WGET_MCP, CURL_MCP],
    instructions=(
        "You are an exploitation specialist conducting a controlled red team engagement "
        "against an intentionally vulnerable OWASP Juice Shop instance.\n\n"

        "Objective:\n"
        "- Leverage ONLY vulnerabilities present in MissionKnowledge.\n"
        "- Chain vulnerabilities where possible to increase impact.\n"
        "- Prioritize SQL injection for this engagement.\n\n"

        "Operational constraints:\n"
        "- Do NOT scan for new vulnerabilities.\n"
        "- Do NOT repeat reconnaissance.\n"
        "- Assume findings are accurate and focus on exploitation.\n\n"

        "Execution rules:\n"
        "- Use MCP tools to perform exploitation steps.\n"
        "- Validate success with concrete evidence (HTTP response, data exfiltration, auth bypass).\n"
        "- Stop exploitation once the stated goal is achieved.\n\n"

        "Output expectations:\n"
        "- Clearly describe each exploitation step taken.\n"
        "- Identify which Vulnerability was used at each step.\n"
        "- Extract and report any credentials or tokens obtained.\n"
        "- If exploitation is not possible, state why concisely.\n"
    )
)

# Summary agent for markdown report
summary_agent = Agent(
    model=LocalModels.nemo_model(),
    instructions=(
    'Summarize the findings into a Markdown style report.'
    )
)
