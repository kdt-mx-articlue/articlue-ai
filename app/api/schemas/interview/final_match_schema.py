from pydantic import BaseModel


class FinalMatchRequest(BaseModel):

    resume_id: int

    job_posting_id: int

    company_name: str

    resume: dict

    interview: dict