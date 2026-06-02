from pydantic import BaseModel
from typing import List, Optional


class JobPostingRequest(BaseModel):

    company_name: str

    job_title: str

    requirements: Optional[str] = ""

    preferences: Optional[str] = ""

    responsibilities: Optional[str] = ""

    tech_stacks: List[str] = []

    team_culture: Optional[str] = ""