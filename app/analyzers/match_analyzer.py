import json

from openai import OpenAI

client = OpenAI()


def analyze_resume_job_match(

    resume_analysis: dict,

    job_analysis: dict

):

    print("🔥 GPT Match Analyzer 실행")

    prompt = f"""

당신은 AI 채용 매칭 전문가입니다.

지원자 분석 결과와 채용공고 분석 결과를 비교하여
아래 JSON 형식으로만 반환하세요. 점수는 생성하지 마세요.

반드시 JSON만 반환하세요.

{{
    "business_fit_reason": "비즈니스 적합성 이유 1줄",
    "action_result_fit_reason": "성과/실행력 적합성 이유 1줄",
    "tech_stack_fit_reason": "기술스택 적합성 이유 1줄",
    "requirement_fit_reason": "자격요건 적합성 이유 1줄",
    "culture_fit_reason": "문화 적합성 이유 1줄",
    "diagnosis": {{
        "diagnosis_summary": "지원자의 전반적 보완 필요 사항 요약 (2-3문장)",
        "tech_stack_weakness": "기술스택 측면의 보완 필요 사항",
        "project_experience_weakness": "프로젝트 경험 측면의 보완 필요 사항",
        "business_result_weakness": "비즈니스 성과/실행력 측면의 보완 필요 사항",
        "domain_understanding_weakness": "도메인 이해도 측면의 보완 필요 사항",
        "improvement_priority": "가장 우선적으로 개선해야 할 항목"
    }},
    "action_plans": [
        {{
            "action_plan_title": "액션 플랜 제목",
            "action_plan_summary": "구체적인 실행 방법 (2-3문장)",
            "recommended_learning": "추천 학습 자료 또는 방법",
            "priority": 1,
            "expected_period": "예상 소요 기간 (예: 2-4주)"
        }},
        {{
            "action_plan_title": "두 번째 액션 플랜 제목",
            "action_plan_summary": "구체적인 실행 방법 (2-3문장)",
            "recommended_learning": "추천 학습 자료 또는 방법",
            "priority": 2,
            "expected_period": "예상 소요 기간"
        }},
        {{
            "action_plan_title": "세 번째 액션 플랜 제목",
            "action_plan_summary": "구체적인 실행 방법 (2-3문장)",
            "recommended_learning": "추천 학습 자료 또는 방법",
            "priority": 3,
            "expected_period": "예상 소요 기간"
        }}
    ]
}}

지원자 분석

{json.dumps(resume_analysis, ensure_ascii=False)}

채용공고 분석

{json.dumps(job_analysis, ensure_ascii=False)}

"""

    response = client.chat.completions.create(

        model="gpt-4.1-mini",

        messages=[

            {
                "role": "system",
                "content": "JSON만 반환"
            },

            {
                "role": "user",
                "content": prompt
            }

        ],

        response_format={
            "type": "json_object"
        }

    )

    return json.loads(
        response.choices[0].message.content
    )
