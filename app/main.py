from dotenv import load_dotenv

from app.analyzers.cover_letter_analyzer import (
    load_cover_letters,
    combine_cover_letters
)

from app.analyzers.semantic_extractor import (
    analyze_cover_letter
)

from app.analyzers.vector_store_service import (
    save_to_vector_db
)


# 환경변수 로드
load_dotenv()


def main():

    # JSON 경로
    json_path = "app/data/docs/resume_001.json"

    # 자기소개서 로드
    cover_letters = load_cover_letters(json_path)

    # 자기소개서 병합
    merged_text = combine_cover_letters(
        cover_letters
    )

    print("\n===== 병합된 자기소개서 =====\n")
    print(merged_text)

    # LLM 분석
    analysis_result = analyze_cover_letter(
        merged_text
    )

    print("\n===== 분석 결과 =====\n")
    print(analysis_result)

    # VectorDB 저장
    save_to_vector_db(
        semantic_text=merged_text,
        analysis_result=analysis_result,
        resume_id=1
    )

    print("\n===== ChromaDB 저장 완료 =====")


if __name__ == "__main__":
    main()