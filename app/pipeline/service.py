from app.analyzers.cover_letter_analyzer import load_cover_letters
from app.analyzers.semantic_extraction import analyze_cover_letter

from app.analyzers.vector_store_service import (
    save_resume_if_not_exists,
    search_similar_jobs
)

from app.services.matching.scoring import weighted_score

from app.analyzers.match_analyzer import (
    analyze_resume_job_match
)

from app.services.jobs.job_service import (
    get_job_by_id,
    get_all_jobs
)

from app.services.matching.match_score_service import (

    calculate_tech_stack_fit,

    calculate_requirement_fit,

    calculate_action_result_fit,

    calculate_business_fit,

    calculate_culture_fit
)

# 전체 공고 수
TOTAL_JOB_COUNT = 484

# GPT 정밀 분석 대상 상위 N개
GPT_TOP_N = 5

def run_pipeline(resume_data: dict, resume_id: int):

    print("▶ resume load 완료")

    data = resume_data["data"]

    # =========================
    # 1. Text Merge (semantic base)
    # =========================
    merged_text = f"""
희망직무
{data.get("desiredJob","")}

소개
{data.get("introduction","")}

기술스택
{" ".join(
        tech.get("techName","")
        for tech in data.get("techStacks",[])
    )}

경력
{" ".join(
        career.get("mainAchievement","")
        for career in data.get("careers",[])
    )}

Github 프로젝트
{" ".join(
        repo.get("projectDescription","")
        for repo in data.get("githubRepositories",[])
    )}

자격증
{" ".join(
        cert.get("certificateName","")
        for cert in data.get("certificates",[])
    )}

자기소개서
{" ".join(
        item.get("content","")
        for cl in data.get("coverLetters",[])
        for item in cl.get("items",[])
    )}
"""

    # =========================
    # 2. LLM 분석 (resume understanding)
    # =========================
    analysis_result = analyze_cover_letter(merged_text)

    # =========================
    # 3. Semantic Search — 전체 공고 대상
    # =========================
    job_matches = search_similar_jobs(
        semantic_text=merged_text,
        resume_id=resume_id,
        top_k=TOTAL_JOB_COUNT
    )

    print(f"\n===================")
    print(f"전체 공고 유사도 검색 완료: {len(job_matches)}개")
    print(f"===================\n")

    # semantic_score: 1위 공고 기준 (score_result 계산용)
    semantic_score = job_matches[0].get("similarity", 0) if job_matches else 0

    # =========================
    # 4. score_result (1위 공고 기준 weighted_score)
    # =========================
    score_result = {
        "skill_score": 0,
        "career_score": 0,
        "education_score": 0,
        "semantic_score": semantic_score,
        "final_score": semantic_score,
        "matched_skills": []
    }

    if job_matches:

        best_job_id = job_matches[0]["job_posting_id"]

        best_job_data = get_job_by_id(best_job_id)

        if best_job_data:

            best_job = {
                "required_skills":
                best_job_data["parsed_result"].get(
                    "tech_stacks",
                    []
                )
            }

            score_result = weighted_score(
                resume_data,
                best_job,
                semantic_score=semantic_score,
                analysis_result=analysis_result
            )

    # =========================
    # 5. Resume Vector 저장
    # =========================
    save_resume_if_not_exists(
        semantic_text=merged_text,
        analysis_result={
            **analysis_result,
            **score_result
        },
        resume_id=resume_id
    )

    # =========================
    # 6. 전체 공고 Rule-based 점수 계산
    #    (action_score, culture_score는 이력서 기준 → 1회만 계산)
    # =========================
    action_score = calculate_action_result_fit(analysis_result)
    culture_score = calculate_culture_fit(analysis_result)

    resume_skills = []
    resume_skills.extend(analysis_result.get("technical_skills", []))
    resume_skills.extend(analysis_result.get("backend_skills", []))

    print(f"▶ action_score={action_score}, culture_score={culture_score}")

    # 전체 공고 한 번에 로드 (파일 1회 접근)
    all_jobs_map = get_all_jobs()

    all_scored = []

    for job in job_matches:

        job_id = job["job_posting_id"]
        job_similarity = job.get("similarity", 0)

        job_data = all_jobs_map.get(job_id)

        if job_data is None:
            print(f"⚠️ job_posting_id={job_id} 없음, 스킵")
            continue

        job_parsed = job_data["parsed_result"]

        tech_score = calculate_tech_stack_fit(
            resume_skills,
            job_parsed.get("tech_stacks", [])
        )

        requirement_score = calculate_requirement_fit(
            resume_data,
            job_parsed
        )

        business_score = calculate_business_fit(
            job_similarity,
            tech_score,
            requirement_score,
            action_score,
            culture_score
        )

        all_scored.append({
            "resume_id": resume_id,
            "job_posting_id": job_id,
            "similarity": job_similarity,
            "tech_score": tech_score,
            "requirement_score": requirement_score,
            "action_score": action_score,
            "culture_score": culture_score,
            "business_score": business_score,
        })

    # 전체 점수 기준 내림차순 정렬
    all_scored.sort(key=lambda x: x["business_score"], reverse=True)

    print(f"\n===================")
    print(f"전체 {len(all_scored)}개 공고 Rule-based 점수 계산 완료")
    print(f"TOP 5:")
    for i, m in enumerate(all_scored[:5], 1):
        print(f"  {i}위 | job_posting_id={m['job_posting_id']} | overall={m['business_score']}")
    print(f"===================\n")

    # =========================
    # 7. 상위 GPT_TOP_N개만 GPT 정밀 분석
    # =========================
    top_ids = set(m["job_posting_id"] for m in all_scored[:GPT_TOP_N])
    gpt_results = {}

    for match in all_scored[:GPT_TOP_N]:

        job_id = match["job_posting_id"]
        job_data = all_jobs_map.get(job_id)

        if job_data is None:
            continue

        print(f"▶ GPT 분석 중: job_posting_id={job_id}")

        ai_result = analyze_resume_job_match(
            resume_analysis=analysis_result,
            job_analysis=job_data["parsed_result"]
        )

        gpt_results[job_id] = ai_result

    print(f"▶ GPT 분석 완료: {len(gpt_results)}개")

    # =========================
    # 8. 전체 final_matches 구성 (484개)
    # =========================
    final_matches = []

    for match in all_scored:

        job_id = match["job_posting_id"]
        gpt = gpt_results.get(job_id, {})

        final_matches.append({

            "resume_id": resume_id,

            "job_posting_id": job_id,

            "analysis": {

                "type": "RESUME",

                "overall_score": match["business_score"],

                "metrics": {

                    "business_fit": {
                        "score": match["business_score"],
                        "reason_text": gpt.get("business_fit_reason", "")
                    },

                    "action_result_fit": {
                        "score": match["action_score"],
                        "reason_text": gpt.get("action_result_fit_reason", "")
                    },

                    "tech_stack_fit": {
                        "score": match["tech_score"],
                        "reason_text": gpt.get("tech_stack_fit_reason", "")
                    },

                    "requirement_fit": {
                        "score": match["requirement_score"],
                        "reason_text": gpt.get("requirement_fit_reason", "")
                    },

                    "culture_fit": {
                        "score": match["culture_score"],
                        "reason_text": gpt.get("culture_fit_reason", "")
                    }

                },

                "diagnosis": gpt.get("diagnosis", None),

                "action_plans": gpt.get("action_plans", [])

            }

        })

    # =========================
    # 9. 결과 반환
    # =========================
    return {
        "resume_id": resume_id,
        "analysis": analysis_result,
        "score": score_result,
        "job_matches": final_matches
    }
