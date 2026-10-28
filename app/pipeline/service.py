import os
from concurrent.futures import ThreadPoolExecutor

from app.analyzers.cover_letter_analyzer import load_cover_letters
from app.analyzers.semantic_extraction import analyze_cover_letter

from app.analyzers.vector_store_service import (
    save_resume_if_not_exists,
    search_similar_jobs
)

from app.services.matching.scoring import weighted_score

from app.services.vector.job_vector_service import get_job_vector_store

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

# 1차 매칭 점수를 계산할 공고 수. 0(기본) = 벡터 DB 의 전체 공고
#  - 화면 검색·상세 분석이 "1차 점수가 있는 공고"를 전제로 하므로 전체를 계산한다
#  - 규칙 기반 점수라 빠르고, 비용이 드는 GPT 정밀 분석은 상위 GPT_TOP_N 건만
MATCH_TOP_K = int(os.environ.get("MATCH_TOP_K", "0"))


def resolve_match_top_k():
    if MATCH_TOP_K > 0:
        return MATCH_TOP_K
    return get_job_vector_store()._collection.count()

# GPT 정밀 분석 대상 상위 N개
GPT_TOP_N = 5

def run_pipeline(resume_data: dict, resume_id: int, analysis_stage: str = "RESUME"):

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
    # 3. Semantic Search — 전체 공고 (MATCH_TOP_K 지정 시 상위 N개)
    # =========================
    job_matches = search_similar_jobs(
        semantic_text=merged_text,
        resume_id=resume_id,
        top_k=resolve_match_top_k()
    )

    print(f"\n===================")
    print(f"후보 공고 유사도 검색 완료: {len(job_matches)}개")
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
    #    (서로 독립적인 호출이라 동시에 실행 → 대기 시간 약 1/N)
    # =========================
    gpt_targets = [
        (match["job_posting_id"], all_jobs_map[match["job_posting_id"]])
        for match in all_scored[:GPT_TOP_N]
        if match["job_posting_id"] in all_jobs_map
    ]

    def analyze_target(target):
        job_id, job_data = target
        print(f"▶ GPT 분석 중: job_posting_id={job_id}")
        return job_id, analyze_resume_job_match(
            resume_analysis=analysis_result,
            job_analysis=job_data["parsed_result"]
        )

    gpt_results = {}

    if gpt_targets:
        with ThreadPoolExecutor(max_workers=len(gpt_targets)) as pool:
            gpt_results = dict(pool.map(analyze_target, gpt_targets))

    print(f"▶ GPT 분석 완료: {len(gpt_results)}개")

    # =========================
    # 8. final_matches 구성 (검색된 전체 공고)
    # =========================
    final_matches = []

    for match in all_scored:

        job_id = match["job_posting_id"]
        gpt = gpt_results.get(job_id, {})

        final_matches.append({

            "resume_id": resume_id,

            "job_posting_id": job_id,

            "analysis": {

                "type": analysis_stage,

                "overall_score": match["business_score"],

                "metrics": {

                    "business_fit": {
                        "score": match["business_score"],
                        "reason_text": gpt.get("business_fit_reason", "-")
                    },

                    "action_result_fit": {
                        "score": match["action_score"],
                        "reason_text": gpt.get("action_result_fit_reason", "-")
                    },

                    "tech_stack_fit": {
                        "score": match["tech_score"],
                        "reason_text": gpt.get("tech_stack_fit_reason", "-")
                    },

                    "requirement_fit": {
                        "score": match["requirement_score"],
                        "reason_text": gpt.get("requirement_fit_reason", "-")
                    },

                    "culture_fit": {
                        "score": match["culture_score"],
                        "reason_text": gpt.get("culture_fit_reason", "-")
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


def run_single_job_pipeline(resume_data: dict, resume_id: int, job_posting_id: int):
    """
    단일 공고에 대한 GPT 정밀 분석만 수행한다.
    전체 484개 벡터 검색 + 점수 계산 없이 GPT 1회만 호출하므로 빠르다.
    기존 COMPANY_RECOMMENDATION 점수는 유지하고,
    PORTFOLIO_DIAGNOSIS + RECOMMENDATION_ACTION 데이터만 생성/갱신한다.
    """

    print(f"▶ 단일 공고 GPT 분석 시작: resume_id={resume_id}, job_posting_id={job_posting_id}")

    data = resume_data["data"]

    # 1. Text Merge (전체 파이프라인과 동일)
    merged_text = (
        f"희망직무\n{data.get('desiredJob', '')}\n\n"
        f"소개\n{data.get('introduction', '')}\n\n"
        f"기술스택\n{' '.join(tech.get('techName', '') for tech in data.get('techStacks', []))}\n\n"
        f"경력\n{' '.join(career.get('mainAchievement', '') for career in data.get('careers', []))}\n\n"
        f"Github 프로젝트\n{' '.join(repo.get('projectDescription', '') for repo in data.get('githubRepositories', []))}\n\n"
        f"자격증\n{' '.join(cert.get('certificateName', '') for cert in data.get('certificates', []))}\n\n"
        f"자기소개서\n{' '.join(item.get('content', '') for cl in data.get('coverLetters', []) for item in cl.get('items', []))}"
    )

    # 2. LLM 이력서 분석
    analysis_result = analyze_cover_letter(merged_text)

    # 3. 대상 공고 데이터 조회
    job_data = get_job_by_id(job_posting_id)
    if job_data is None:
        raise ValueError(f"job_posting_id={job_posting_id} 공고 데이터를 찾을 수 없습니다.")

    # 4. GPT 정밀 분석 (단 1회)
    print(f"▶ GPT 분석 중: job_posting_id={job_posting_id}")
    ai_result = analyze_resume_job_match(
        resume_analysis=analysis_result,
        job_analysis=job_data["parsed_result"]
    )

    print(f"▶ 단일 공고 GPT 분석 완료: job_posting_id={job_posting_id}")

    return {
        "resume_id": resume_id,
        "job_posting_id": job_posting_id,
        "diagnosis": ai_result.get("diagnosis"),
        "action_plans": ai_result.get("action_plans", []),
        "reasons": {
            "business_fit":      ai_result.get("business_fit_reason", "-"),
            "action_result_fit": ai_result.get("action_result_fit_reason", "-"),
            "tech_stack_fit":    ai_result.get("tech_stack_fit_reason", "-"),
            "requirement_fit":   ai_result.get("requirement_fit_reason", "-"),
            "culture_fit":       ai_result.get("culture_fit_reason", "-"),
        },
    }
