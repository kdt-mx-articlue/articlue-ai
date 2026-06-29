import json

from openai import OpenAI

from app.services.interview.interview_score_service import (
    apply_interview_scores,
    calculate_final_overall_score
)

client = OpenAI()


def generate_final_action_plans(final_metrics, company_name):
    """
    면접 후 최종 메트릭을 바탕으로 GPT가 액션 플랜을 생성한다.
    """
    prompt = f"""
당신은 AI 취업 코치입니다.

지원자가 '{company_name}' 면접을 마쳤습니다.
아래는 이력서 분석과 면접 결과를 합산한 최종 역량 점수입니다.

점수가 낮은 항목을 중심으로, 지원자가 실제로 실행할 수 있는 액션 플랜 2~3개를 생성하세요.

반드시 아래 JSON 형식으로만 반환하세요.

{{
  "action_plans": [
    {{
      "category": "TECH",
      "action_plan_title": "제목 (간결하게)",
      "action_plan_summary": "구체적 실행 방법 (1~2줄)",
      "recommended_learning": "추천 학습 자료 또는 방법",
      "priority": 1,
      "expected_period": "2-4주"
    }}
  ]
}}

category는 "TECH" | "PROJECT" | "BUSINESS" | "DOMAIN" 중 하나입니다.

최종 역량 점수:
{json.dumps(final_metrics, ensure_ascii=False)}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": '반드시 {"action_plans": [...]} 형식의 JSON만 반환'},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    raw = json.loads(response.choices[0].message.content)

    if isinstance(raw.get("action_plans"), list):
        return raw["action_plans"]
    # 혹시 다른 키로 감싼 경우 fallback
    for key in ("plans", "result", "items", "recommendations"):
        if isinstance(raw.get(key), list):
            return raw[key]
    return []


def build_final_match(
    resume_data,
    interview_data,
    company_name=""
):

    final_metrics = apply_interview_scores(
        resume_data["metrics"],
        interview_data
    )

    overall_score = calculate_final_overall_score(
        final_metrics
    )

    action_plans = generate_final_action_plans(final_metrics, company_name)

    return {
        "overall_score": overall_score,
        "metrics": final_metrics,
        "action_plans": action_plans,
    }