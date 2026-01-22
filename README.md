# Automating Exploitation with Agentic Systems - Workshop

**This workshop demonstrates Agentic AI in offensive cybersecurity roles solely for educational use and must not be used against any system without explicit permission.**

## Exercise 3 - E-Commerce DB Exfiltration

This repository demonstrates a collaborative system of agents led by an orchestration agent making decisions based on updated context from the team. 

- **Mission Agent**: Orchestration agent overseeing the engagement.
- **Recon Agents**: Performs reconnaissance against target based on provided goals and overall team goal.
- **Summary**: Provides a concise report of the recon outout.
- **Exploit**: Performs on target action with summarized report and mission context to reach overall goal.

Outputs summary report and, with any luck, the requested sensitive data from the target.

## Tools Used

- Series of MCP connected tools 
- Mixed frontier model use GPT-5.2, Opus-4.5, and local model for summarization
- Asynchronous teaming of agents
- Mission Knowledge for overall context
- Pydantic Logfire for observability 

## Purpose

Highlights capabilities of collaborative agents with MCP tool access.

## Installation

**Note Logfire requires an account to use however they have a VERY generous free tier**

1. git clone https://github.com/kwnge/2026-ai-sym-cyber-exercise3.git
2. cd 2026-ai-sym-cyber-exercise3
3. uv sync
4. source .venv/bin/activate
5. logfire auth ## if using logfire
6. Create .env file with API keys to LLM providers
7. uv run main.py

## Usage

1. Initalize and confirm your local model is available at address for LOCAL_MODEL definition. 
2. Initialize your mission dependencies with the target, goal and target information. 
3. The Recon agents will look for public endpoints and possible SQL injection opportunities against the target. 
5. A summary is created along with an updated mission context that is all passed to the exploit agent.
6. The Exploit agent proceeds to exploit SQLi opportunities with end goal of table exfilatration.

## Ethical Considerations

This tool is provided for educational purposes only. It should be used exclusively in controlled lab environments to improve defensive security measures. Unauthorized use on systems without explicit permission is prohibited.

---

*Created for 2026 AI Symposium workshop to highlight agentic capability. Use responsibly.*