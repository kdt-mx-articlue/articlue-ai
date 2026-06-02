from app.analyzers.cover_letter_analyzer import (
    load_cover_letters,
    combine_cover_letters
)

from app.analyzers.semantic_extraction import (
    analyze_cover_letter
)

from app.analyzers.vector_store_service import (
    save_to_vector_db
)

from app.services.matching.scoring import weighted_score


def run_pipeline(json_path: str, resume_id: int):

    # 1. 데이터 로드
    cover_letters = load_cover_letters(json_path)
    merged_text = combine_cover_letters(cover_letters)

    # 2. LLM 분석
    analysis_result = analyze_cover_letter(merged_text)

    # 3. scoring (너가 만든 weighted_score 구조 사용)
    dummy_job = {
        "required_skills": ["Python", "FastAPI", "MySQL"]
    }

    score_result = weighted_score(
        analysis_result,
        dummy_job
    )

    # 4. DB 저장
    save_to_vector_db(
        semantic_text=merged_text,
        analysis_result={
            **analysis_result,
            **score_result
        },
        resume_id=resume_id
    )

    return {
        "resume_id": resume_id,
        "analysis": analysis_result,
        "score": score_result
    }