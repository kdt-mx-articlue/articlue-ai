from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from app.services.cover_letter.cover_letter_generator import (
    extract_questions,
    generate_cover_letter,
    DEFAULT_QUESTIONS,
)

router = APIRouter()


# ─── 문항 추출 ───────────────────────────────────────────────
class ExtractQuestionsRequest(BaseModel):
    jobDescription: str


@router.post("/cover-letter/extract-questions")
def extract(req: ExtractQuestionsRequest):
    """
    채용공고 텍스트에서 자소서 문항을 추출합니다.
    추출 실패 시 기본 5문항을 반환합니다.
    프론트에서 이 문항을 사용자에게 보여주고 수정할 수 있게 합니다.
    """
    try:
        questions = extract_questions(req.jobDescription)
        return {
            "success": True,
            "questions": questions if questions else DEFAULT_QUESTIONS,
            "source": "extracted" if questions else "default",
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {
            "success": True,
            "questions": DEFAULT_QUESTIONS,
            "source": "default",
        }


# ─── 자소서 생성 ─────────────────────────────────────────────
class CoverLetterRequest(BaseModel):
    resumeData: Dict[str, Any]
    companyName: str
    jobTitle: str
    jobDescription: Optional[str] = ""
    questions: Optional[List[str]] = None  # 사용자가 확인/수정한 문항 (없으면 자동 결정)


@router.post("/cover-letter/generate")
def generate(req: CoverLetterRequest):
    """
    사용자의 이력서와 범용 자소서를 기반으로
    지원 기업/직무에 맞게 자소서를 재구성합니다.
    """
    try:
        result = generate_cover_letter(
            resume_data=req.resumeData,
            company_name=req.companyName,
            job_title=req.jobTitle,
            job_description=req.jobDescription or "",
            custom_questions=req.questions,
        )
        return {
            "success": True,
            "questions": result["questions"],
            "source": result["source"],
            "items": result["items"],
        }
    except Exception as e:
        import traceback
        print("❌ COVER LETTER ERROR")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
