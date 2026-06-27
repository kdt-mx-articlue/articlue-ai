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

지원자 분석 결과와 채용공고 분석 결과를 비교하세요.

점수는 생성하지 마세요.

아래 항목을 모두 포함한 JSON을 반환하세요.

1. 항목별 이유 (1줄씩)
- business_fit_reason
- action_result_fit_reason
- tech_stack_fit_reason
- requirement_fit_reason
- culture_fit_reason

2. 보완 필요 진단 (diagnosis)
- diagnosis_summary: 전체 보완 필요 요약 (1~2줄)
- tech_stack_weakness: 기술스택 보완 필요 사항 (없으면 null)
- project_experience_weakness: 프로젝트 경험 보완 필요 사항 (없으면 null)
- business_result_weakness: 비즈니스 성과 보완 필요 사항 (없으면 null)
- domain_understanding_weakness: 도메인 이해도 보완 필요 사항 (없으면 null)
- improvement_priority: 가장 우선 보완해야 할 항목 키워드 (예: "기술스택")

3. 액션 플랜 (action_plans): 2~3개 배열
- category: "TECH" | "PROJECT" | "BUSINESS" | "DOMAIN" 중 하나
- action_plan_title: 액션 제목 (간결하게)
- action_plan_summary: 구체적 실행 방법 (1~2줄)
- recommended_learning: 추천 학습 자료 또는 방법
- priority: 1부터 시작하는 우선순위 숫자
- expected_period: 예상 소요 기간 (예: "2-4주")

반드시 JSON만 반환하세요.

{{
    "business_fit_reason": "...",
    "action_result_fit_reason": "...",
    "tech_stack_fit_reason": "...",
    "requirement_fit_reason": "...",
    "culture_fit_reason": "...",
    "diagnosis": {{
        "diagnosis_summary": "...",
        "tech_stack_weakness": "...",
        "project_experience_weakness": "...",
        "business_result_weakness": null,
        "domain_understanding_weakness": null,
        "improvement_priority": "기술스택"
    }},
    "action_plans": [
        {{
            "category": "TECH",
            "action_plan_title": "TypeScript 학습",
            "action_plan_summary": "공식 문서와 실습 프로젝트를 통해 TypeScript 기초를 익히세요.",
            "recommended_learning": "TypeScript 공식 문서, Udemy 강의",
            "priority": 1,
            "expected_period": "2-4주"
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
