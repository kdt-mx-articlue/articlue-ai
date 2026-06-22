PROMPT_VERSION = "v1.1"

SYSTEM_PROMPT = """당신은 AI 챗봇이 참고할 배경지식을 생성하는 전문가입니다.
다음 기사 요약과 메가 트렌드를 바탕으로 오늘의 IT 동향을 하나의 Context 문서로 작성하세요.

[작성 규칙]
1. 여러 기사를 하나의 흐름으로 통합하여 트렌드 중심으로 정리합니다.
2. 개발자 취업 준비생이 알아야 하는 내용(IT 기술 및 산업 변화)만 남깁니다.
3. 기사 원문을 그대로 복사하지 않고 정보를 압축하여 작성합니다.
4. AI(챗봇)가 읽고 컨텍스트를 파악하기 쉽도록 계층적 구조의 Markdown을 사용합니다.
5. 제공된 기사와 트렌드에 없는 사실은 절대로 추가하지 않으며, 오직 제공된 데이터만 사용합니다.

반드시 유효한 JSON만 출력한다.

문자열 내부의 줄바꿈은 실제 Enter를 사용하지 말고 반드시 \\n 으로 이스케이프한다.

Markdown을 사용하더라도 실제 줄바꿈이 아닌 \\n 문자만 사용한다.

설명은 절대 하지 않는다.

{
    "promptContext": {
        "rawText": "# 오늘의 IT 트렌드 및 기사 컨텍스트\n\n## 주요 트렌드\n1. ...\n\n## 종합 컨텍스트\n..."
    }
}"""

def build_prompt_context_prompt(articles: list[dict], trends: list[dict]) -> dict:
    MAX_ARTICLES = 20
    
    # 1. 트렌드 조립
    trend_parts = []
    for t in trends:
        trend_parts.append(f"- [{t.get('topic')}] {t.get('description')}")
    trend_str = "\n".join(trend_parts)

    # 2. 기사 조립 (### 기사 X 계층 구조 적용)
    article_parts = []
    for idx, article in enumerate(articles[:MAX_ARTICLES], 1):
        title = article.get("title", "제목 없음")
        summary_data = article.get("summary")
        summary_str = " ".join(summary_data.get("text", [])) if summary_data and isinstance(summary_data.get("text"), list) else ""
        
        article_parts.append(
            f"### 기사 {idx}\n"
            f"제목: {title}\n"
            f"요약: {summary_str}\n"
        )
    article_str = "\n".join(article_parts)

    user_prompt = f"[메가 트렌드]\n{trend_str}\n\n[주요 기사 요약]\n{article_str}"
    
    return {
        "system": SYSTEM_PROMPT,
        "user": user_prompt.strip()
    }