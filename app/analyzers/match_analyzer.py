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

지원자 분석 결과와
채용공고 분석 결과를 비교하세요.

점수는 생성하지 마세요.

아래 항목별 이유(reason)만 1줄 작성하세요.

1. business_fit_reason
2. action_result_fit_reason
3. tech_stack_fit_reason
4. requirement_fit_reason
5. culture_fit_reason

반드시 JSON만 반환하세요.

예시

{{
    "business_fit_reason":"...",
    "action_result_fit_reason":"...",
    "tech_stack_fit_reason":"...",
    "requirement_fit_reason":"...",
    "culture_fit_reason":"..."
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