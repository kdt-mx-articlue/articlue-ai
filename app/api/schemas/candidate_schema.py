from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class ResumeRequest(BaseModel):

    name: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    education: Optional[str] = None

    skills: List[str] = Field(default_factory=list)

    projects: List[str] = Field(default_factory=list)

    cover_letter: str = Field(
        ...,
        min_length=10,
        max_length=2000
    )

    # -------------------------
    # 1) skills 정제
    # -------------------------
    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, v):
        cleaned = [
            skill.strip().lower()
            for skill in v
            if isinstance(skill, str) and skill.strip()
        ]
        return list(set(cleaned))  # 중복 제거

    # -------------------------
    # 2) projects 정제
    # -------------------------
    @field_validator("projects")
    @classmethod
    def normalize_projects(cls, v):
        return [
            p.strip()
            for p in v
            if isinstance(p, str) and p.strip()
        ]

    # -------------------------
    # 3) education 정제
    # -------------------------
    @field_validator("education")
    @classmethod
    def normalize_education(cls, v):
        if v is None:
            return v

        v = v.strip()
        return v if v else None

    # -------------------------
    # 4) cover_letter 강화 검증
    # -------------------------
    @field_validator("cover_letter")
    @classmethod
    def validate_cover_letter(cls, v):
        text = v.strip()

        if len(text) < 10:
            raise ValueError("cover_letter too short")

        # 의미 없는 반복 문자 방지
        if len(set(text)) < 5:
            raise ValueError("cover_letter looks invalid")

        return text