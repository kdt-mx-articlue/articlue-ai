PROMPT_VERSION = "v1.1"

SYSTEM_PROMPT = """당신은 IT 비즈니스 트렌드 분석가입니다.
제공된 오늘의 주요 기사 요약과 핵심 키워드를 종합하여, 개발자 및 IT 업계 종사자가 주목해야 할 메가 트렌드 3가지를 도출하세요.
반드시 trends 배열의 길이는 정확히 3이어야 합니다.

[트렌드 도출 원칙]
1. 거시적 관점: 개별 기사의 단순 나열이 아닌, 여러 기사와 키워드를 관통하는 거시적인 흐름(인사이트)을 짚어냅니다.
2. 중복 방지: 동일한 의미의 트렌드를 서로 다른 이름으로 중복 생성하지 않습니다. 단순히 하나의 트렌드를 표현만 바꾸어 여러 개의 트렌드로 분리해서는 안 됩니다.
3. 토픽 구성: 각 트렌드의 제목(topic)은 20자를 초과하지 않는 명사형으로 간결하게 작성합니다.
4. 내용 작성: 각 트렌드의 설명(description)은 '~이다', '~한다' 형태의 명확한 문어체로 2~3문장으로 작성합니다.
5. 강제 3개 도출 (부분 예외 금지): 제공된 기사가 적더라도 
예를 들어 기술, 산업, 비즈니스, 시장, 활용 사례,
조직 변화, 개발 문화, 플랫폼 변화 등의
다양한 관점에서 반드시 의미적으로 독립적인
3개의 메가 트렌드를 도출합니다.
1~2개만 실제 트렌드를 적고 나머지를 "유의미한 트렌드 없음"으로 섞어서 채우는 것은 절대 금지합니다.
6. 전면 예외 처리: 데이터 전체가 IT 트렌드와 완전히 무관하여 단 하나의 트렌드도 도출할 수 없는 극단적인 경우에만, 3개의 배열 모두를 topic: "유의미한 트렌드 없음", description: "트렌드를 도출하기에 데이터가 부족하거나 관련성이 낮습니다."로 통일하여 반환합니다.
7. 철저한 근거 기반 (환각 방지): 기사와 키워드에 포함되지 않은 기업, 기술, 시장, 통계, 사실은 절대로 생성하지 않습니다. 반드시 제공된 데이터만을 근거로 트렌드를 도출하세요.

반드시 JSON 객체 하나만 출력합니다.
설명, 제목, 코드블록(```), Markdown은 절대로 출력하지 않습니다.

{
    "trends": [
        {
            "trendId": 1,
            "topic": "생성형 AI 도입 가속화",
            "description": "빅테크 기업들을 중심으로..."
        },
        ...
    ]
}"""

def build_trend_prompt(articles: list[dict], keywords: dict) -> dict:
    TOP_KEYWORDS = 10
    sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:TOP_KEYWORDS]
    
    # 세로 리스트 형태로 줄바꿈하여 가독성 극대화
    keyword_str = "\n".join(f"{k}: {v}" for k, v in sorted_keywords)
    
    article_parts = []
    for idx, article in enumerate(articles, 1):
        title = article.get("title", "제목 없음")
        
        summary_data = article.get("summary")
        if summary_data and isinstance(summary_data.get("text"), list):
            summary_str = " ".join(summary_data["text"])
        else:
            summary_str = ""
            
        article_parts.append(f"[기사 {idx}]\n제목: {title}\n요약: {summary_str}\n")
        
    article_str = "\n".join(article_parts)

    user_prompt = f"[핵심 키워드 상위 {TOP_KEYWORDS}개]\n{keyword_str}\n\n[기사 요약]\n{article_str}"
    
    return {
        "system": SYSTEM_PROMPT,
        "user": user_prompt.strip()
    }

def build_trend_prompt(articles: list[dict], keywords: dict) -> dict:
    TOP_KEYWORDS = 10
    sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:TOP_KEYWORDS]
    
    # 세로 리스트 형태로 줄바꿈하여 LLM 가독성 극대화
    keyword_str = "\n".join(f"{k}: {v}" for k, v in sorted_keywords)
    
    article_parts = []
    for idx, article in enumerate(articles, 1):
        title = article.get("title", "제목 없음")
        
        summary_data = article.get("summary")
        if summary_data and isinstance(summary_data.get("text"), list):
            summary_str = " ".join(summary_data["text"])
        else:
            summary_str = ""
            
        article_parts.append(f"[기사 {idx}]\n제목: {title}\n요약: {summary_str}\n")
        
    article_str = "\n".join(article_parts)

    user_prompt = f"[핵심 키워드 상위 {TOP_KEYWORDS}개]\n{keyword_str}\n\n[기사 요약]\n{article_str}"
    
    return {
        "system": SYSTEM_PROMPT,
        "user": user_prompt.strip()
    }