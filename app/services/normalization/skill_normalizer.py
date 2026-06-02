import re

from typing import (
    List,
    Dict,
    Set
)


class SkillNormalizer:
    """
    기술 스택 정규화 모듈

    기능:
    - 소문자 통일
    - alias 매핑
    - 특수문자 정리
    - 중복 제거
    - 리스트/텍스트 대응
    """

    def __init__(self):

        # =========================
        # 기술 alias 매핑
        # =========================
        self.alias_map: Dict[str, str] = {

            # =====================
            # JavaScript
            # =====================
            "js": "javascript",
            "javascript": "javascript",

            # =====================
            # TypeScript
            # =====================
            "ts": "typescript",
            "typescript": "typescript",

            # =====================
            # Python
            # =====================
            "py": "python",
            "python": "python",

            # =====================
            # Node
            # =====================
            "node": "nodejs",
            "node.js": "nodejs",
            "nodejs": "nodejs",

            # =====================
            # FastAPI
            # =====================
            "fast api": "fastapi",
            "fast-api": "fastapi",
            "fastapi": "fastapi",

            # =====================
            # React
            # =====================
            "react.js": "react",
            "reactjs": "react",
            "react": "react",

            # =====================
            # Express
            # =====================
            "express.js": "express",
            "expressjs": "express",
            "express": "express",

            # =====================
            # Spring
            # =====================
            "spring boot": "springboot",
            "spring-boot": "springboot",
            "springboot": "springboot",
            "spring": "spring",

            # =====================
            # DB
            # =====================
            "mysql": "mysql",
            "my sql": "mysql",

            "postgres": "postgresql",
            "postgresql": "postgresql",

            "mongo": "mongodb",
            "mongodb": "mongodb",

            # =====================
            # AI / ML
            # =====================
            "ml": "machine learning",
            "machine learning": "machine learning",

            "ai": "artificial intelligence",
            "artificial intelligence": (
                "artificial intelligence"
            ),

            "sklearn": "scikit-learn",
            "scikit learn": "scikit-learn",
            "scikit-learn": "scikit-learn",

            "lang chain": "langchain",
            "langchain": "langchain",

            "chroma db": "chromadb",
            "chromadb": "chromadb",

            "rag": "rag",

            "llm": "llm",

            # =====================
            # C 계열
            # =====================
            "c++": "cpp",
            "cpp": "cpp",

            "c#": "csharp",
            "csharp": "csharp",

            # =====================
            # Infra
            # =====================
            "docker": "docker",

            "k8s": "kubernetes",
            "kubernetes": "kubernetes",

            "aws": "aws",

            "gcp": "gcp"
        }

        # =========================
        # 문자 정리 패턴
        # =========================
        self.clean_pattern = re.compile(
            r"[^a-z0-9+#. ]+"
        )

    # =============================
    # 기본 문자열 정리
    # =============================
    def _clean(
        self,
        skill: str
    ) -> str:

        skill = skill.lower().strip()

        skill = self.clean_pattern.sub(
            "",
            skill
        )

        skill = re.sub(
            r"\s+",
            " ",
            skill
        )

        return skill.strip()

    # =============================
    # alias 적용
    # =============================
    def _apply_alias(
        self,
        skill: str
    ) -> str:

        return self.alias_map.get(
            skill,
            skill
        )

    # =============================
    # 단일 스킬 정규화
    # =============================
    def normalize_one(
        self,
        skill: str
    ) -> str:

        if not skill:
            return ""

        cleaned = self._clean(skill)

        normalized = self._apply_alias(
            cleaned
        )

        return normalized

    # =============================
    # 리스트 정규화
    # =============================
    def normalize_list(
        self,
        skills: List[str]
    ) -> List[str]:

        normalized_set: Set[str] = set()

        for skill in skills:

            if not skill:
                continue

            normalized = (
                self.normalize_one(skill)
            )

            if normalized:
                normalized_set.add(
                    normalized
                )

        return list(normalized_set)

    # =============================
    # 문자열 blob 처리
    # =============================
    def normalize_text_blob(
        self,
        text: str
    ) -> List[str]:

        if not text:
            return []

        raw_skills = re.split(
            r"[,\|/]",
            text
        )

        return self.normalize_list(
            raw_skills
        )


# =================================
# Singleton
# =================================
skill_normalizer = SkillNormalizer()


# =================================
# 외부 사용 함수
# =================================
def normalize_skills(
    skills: List[str]
) -> List[str]:

    return skill_normalizer.normalize_list(
        skills
    )


def normalize_skill(
    skill: str
) -> str:

    return skill_normalizer.normalize_one(
        skill
    )


def normalize_skill_text(
    text: str
) -> List[str]:

    return (
        skill_normalizer.normalize_text_blob(
            text
        )
    )