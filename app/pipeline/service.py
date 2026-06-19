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
    get_job_by_id
)

from app.services.matching.match_score_service import (

    calculate_tech_stack_fit,

    calculate_requirement_fit,

    calculate_action_result_fit,

    calculate_business_fit,
    
    calculate_culture_fit
)

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
    # 3. Semantic Search (job matching base)
    # =========================
    job_matches = search_similar_jobs(
        semantic_text=merged_text,
        resume_id=resume_id,
        top_k=5
    )


    print("\n===================")
    print("job_matches 결과")
    print("===================")

    for idx, job in enumerate(job_matches, start=1):

        print(
            f"{idx}위 | "
            f"job_posting_id={job['job_posting_id']} | "
            f"similarity={job['similarity']}"
        )

    print("===================\n")

    # semantic_score 연결 (핵심 수정)
    semantic_score = job_matches[0].get(
    "similarity",
    0
)
 # =========================
 # 4. score 계산용 최고 매칭 공고
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

        best_job_data = get_job_by_id(
            best_job_id
        )

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

            print("score_result =", score_result)


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
# 6. GPT Job-level Matching
# =========================
    final_matches = []

    for job in job_matches:


        job_similarity = job.get(
        "similarity",
        0
    )

        print(
            "semantic =",
            job_similarity
        )

        print("매칭 Job :", job["job_posting_id"])

        job_data = get_job_by_id(
            job["job_posting_id"]
        )

        if job_data is None:
            print("job_data 없음")
            continue

        ai_result = analyze_resume_job_match(

            resume_analysis=analysis_result,

            job_analysis=job_data["parsed_result"]

        )

        job_parsed = job_data["parsed_result"]

        print("tech_stacks =")
        print(
            job_parsed.get(
                "tech_stacks",
                []
            )
        )

        resume_skills = []

        resume_skills.extend(
            analysis_result.get(
                "technical_skills",
                []
            )
        )

        resume_skills.extend(
            analysis_result.get(
                "backend_skills",
                []
            )
        )

        tech_score = calculate_tech_stack_fit(

            resume_skills,

            job_parsed.get(
                "tech_stacks",
                []
            )
        )

        requirement_score = (
            calculate_requirement_fit(
                resume_data,
                job_parsed
            )
        )

        action_score = (
            calculate_action_result_fit(
                analysis_result
            )
        )

        culture_score = calculate_culture_fit(
            analysis_result
            )

        business_score = (
            calculate_business_fit(
                
                job_similarity,

                tech_score,

                requirement_score,

                action_score,

                culture_score

            )
        )

        print("tech =", tech_score)
        print("requirement =", requirement_score)
        print("action =", action_score)
        print("business =", business_score)

    final_matches.append({

        "resume_id": resume_id,

        "job_posting_id": job["job_posting_id"],

        "analysis": {

            "type": "RESUME",

            "overall_score": business_score,

            "metrics": {

                "business_fit": {
                    "score": business_score,
                    "reason_text": ai_result.get(
                        "business_fit_reason",
                        ""
                    )
                },

                "action_result_fit": {
                    "score": action_score,
                    "reason_text": ai_result.get(
                        "action_result_fit_reason",
                        ""
                    )
                },

                "tech_stack_fit": {
                    "score": tech_score,
                    "reason_text": ai_result.get(
                        "tech_stack_fit_reason",
                        ""
                    )
                },

                "requirement_fit": {
                    "score": requirement_score,
                    "reason_text": ai_result.get(
                        "requirement_fit_reason",
                        ""
                    )
                },

                "culture_fit": {
                    "score": culture_score,
                    "reason_text": ai_result.get(
                        "culture_fit_reason",
                        ""
                    )
                }

            }

        }

    })

    # =========================
    # 7. 결과 반환
    # =========================
    return {
        "resume_id": resume_id,
        "analysis": analysis_result,
        "score": score_result,
        "job_matches": final_matches
    }