from pydantic import BaseModel
from typing import List


class MatchResponse(BaseModel):

    job_id: int

    company_name: str

    job_title: str

    matching_score: float

    matched_skills: List[str]