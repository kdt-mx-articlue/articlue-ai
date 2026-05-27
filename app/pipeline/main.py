import argparse
from dotenv import load_dotenv

from app.analyzers.cover_letter_analyzer import load_cover_letters, combine_cover_letters
from app.analyzers.semantic_extraction import analyze_cover_letter
from app.analyzers.vector_store_service import save_to_vector_db

load_dotenv()


def main(json_path: str, resume_id: int):

    cover_letters = load_cover_letters(json_path)
    merged_text = combine_cover_letters(cover_letters)

    print("\n===== 병합된 자기소개서 =====\n")
    print(merged_text)

    analysis_result = analyze_cover_letter(merged_text)

    print("\n===== 분석 결과 =====\n")
    print(analysis_result)

    save_to_vector_db(
        semantic_text=merged_text,
        analysis_result=analysis_result,
        resume_id=resume_id
    )

    print("\n===== ChromaDB 저장 완료 =====")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True)
    parser.add_argument("--id", type=int, default=1)

    args = parser.parse_args()

    main(args.json, args.id)