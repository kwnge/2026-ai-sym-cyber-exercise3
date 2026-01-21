from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from typing import Dict, List, Set

class AttackVector(BaseModel):
    '''
    Defines an attack vector for use in offensive engagement.
    '''
    type: str = Field(description="The Attack Vector type: SQLi, Information Disclosure, Misconfiguration, Exposed Credentials") 
    explicit_path: str = Field(description="The path to the Attack Vector I.G. http://10.10.26.1/rest/products/search?q=")
    payload: str = Field(description="The payload to exploit the Attack Vector or what was used.  GET /robots.txt or q=apple%VPv")
    confirmed: bool = Field(description="During any of the stages this Attack Vector was confirmed seen as exploitable")

class ExploitResults(BaseModel):
    completed_steps: List[str] = Field(description="Steps taken to complete exploit process against an Attack Vector")

class MissionKnowledge(BaseModel):
    attack_surface: Dict[str, List[str]] = Field(default_factory=dict) 
    identified_vulns: List[AttackVector] = Field(default_factory=list)
    credentials_found: List[str] = Field(default_factory=list)
    completed_steps: Set[ExploitResults] = Field(default_factory=set)

@dataclass
class Deps:
    target: str
    goal: str
    target_information: str
    knowledge: MissionKnowledge = field(default_factory=MissionKnowledge) 