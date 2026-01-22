import logfire
import asyncio
from dotenv import load_dotenv
# Load environment variables from .env filetract
load_dotenv()

from deps import Deps
from agents import mission_agent
from tools import run_parallel_recon, run_exploitation, run_summary_report

# Configure Logfire tracing
logfire.configure(
    environment="2026 AI Symposium",
    service_name="E-Commerce DB Exfil - Exercise 3",
    send_to_logfire="if-token-present"
)
logfire.instrument_pydantic_ai()


async def main():
    # initialize main state
    mission_deps = Deps(
        target="10.26.1.11:80",
        goal="Extract 2 high value tables via SQLi",
        target_information="Your target is an OWASP Juice shop instance."
    )
    logfire.info('Starting mission agent!')
    # Run master agent
    result = await mission_agent.run(
        'Begin the red team engagement! Start with reconnaissance to map the attack surface. '
        f'Your target is {mission_deps.target} with the explicit goal of {mission_deps.goal}.'
        'After each piece of the engagement, please create a summary report of findings. For '
        'example if there is a recon stage, please create summary report of findings and exploit results.',
        deps=mission_deps
    )
    print("\n---AGENT RESPONSE---")
    print(result.output)
    
    with open('mission_agent_summary.md', 'w') as f:
        f.write(result.output)

    print("\n---FINAL STATE---")
    print(mission_deps.knowledge.model_dump_json(indent=2))

    
if __name__ == "__main__":

    asyncio.run(main())