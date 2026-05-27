from app.analyzers.cover_letter_analyzer import (
    load_cover_letters,
    combine_cover_letters
)

from app.analyzers.semantic_extraction import analyze_cover_letter
from app.analyzers.vector_store_service import save_to_vector_db


def run_pipeline(json_path: str, resume_id: int):

    # 1. 데이터 로드
    cover_letters = load_cover_letters(json_path)

    # 2. 전처리 (병합)
    merged_text = combine_cover_letters(cover_letters)

    # 3. LLM 분석
    analysis_result = analyze_cover_letter(merged_text)

    # 4. VectorDB 저장
    save_to_vector_db(
        semantic_text=merged_text,
        analysis_result=analysis_result,
        resume_id=resume_id
    )

    # 5. 결과 반환
    return {
        "resume_id": resume_id,
        "merged_text": merged_text,
        "analysis_result": analysis_result
    }