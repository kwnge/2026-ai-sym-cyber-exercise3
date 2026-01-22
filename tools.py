import asyncio
import logfire
from pydantic_ai import RunContext, AgentRunResult
from deps import Deps, AttackVector, MissionKnowledge, ExploitResults

from agents import recon_endpoint_agent, recon_sqli_agent, summary_agent, exploit_agent
import agents

# Check Deps for latest class model
async def _update_knowledge_from_results(
    knowledge: MissionKnowledge,
    results: list[AgentRunResult]
) -> None:
    logfire.info('Mission knowledge (context) was updated!')
    v: AttackVector
    seen = {(v.type, v.explicit_path) for v in knowledge.identified_vulns}

    for run_result in results:
        for v in run_result.output:
            if (v.type, v.explicit_path) not in seen:
                knowledge.identified_vulns.append(v)
                knowledge.attack_surface.setdefault(v.explicit_path, [])
                if v.type not in knowledge.attack_surface[v.explicit_path]:
                    knowledge.attack_surface[v.explicit_path].append(v.type)

                seen.add((v.type, v.explicit_path))

@agents.mission_agent.tool
async def run_parallel_recon(ctx: RunContext[Deps]) -> list:
    """
    Orchestrates initial recon phase against target and updates MissionKnowledge
    with findings.
    """
    logfire.info(f'Parallel recon tool was called for target: {ctx.deps.target}')
    knowledge = ctx.deps.knowledge

    # Define tasks for async gather
    tasks = [
        recon_endpoint_agent.run(f"Identify 5 highly vulnerable public endpoints on target {ctx.deps.target}. Only focus on typical endpoints. Don't search for everything as we are under a time constraint. Additional information: \n{ctx.deps.target_information}", deps=ctx.deps),
        recon_sqli_agent.run(f"Test and identify for SQLi weaknesses on target {ctx.deps.target}. Additional information: \n{ctx.deps.target_information}", deps=ctx.deps),
    ]

    # Run tasks simultaneously
    results = await asyncio.gather(*tasks)

    logfire.info(f'{len(tasks)} recon tasks were completed!')

    await _update_knowledge_from_results(knowledge=knowledge, results=results)

    return results

@agents.mission_agent.tool
async def run_exploitation(ctx: RunContext[Deps]) -> ExploitResults:
    """
    Performs exploitation on OWASP Juice shop target pulling information on high or critical targets 
    from mission knowledge .
    """
    logfire.info(f'Exploitation agent called!')
    results = await exploit_agent.run(
        f'Perform exploitation of target: {ctx.deps.target}. '
        'Please prioritize SQL injection where possible'
        f'\nMission Knowledge: {ctx.deps.knowledge}'
    )

    with open('exploitation_summary.md', 'w') as f:
        f.write(results.output)

    print(f"RESULTS FROM EXPLOITATION: {results.output}")

@agents.mission_agent.tool
async def run_summary_report(ctx:RunContext[Deps]) -> str:
    """
    Generates summary report on findings into a Markdown style.
    """
    logfire.info('Summary agent called!')
    results = await summary_agent.run(
        f"Generate summary report on latest MissionKnowledge output: {ctx.deps.knowledge}"
        "\n Include Detailed findings review, Advisement on exploitation next steps, "
        "and possible operation security steps to remove exploitation events produced. "
    )
    
    with open('mission_summary.md', 'w') as f:
        f.write(results.output)

    return results.output
