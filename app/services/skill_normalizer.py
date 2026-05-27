import re
from typing import List, Dict, Set


class SkillNormalizer:
    """
    기술 스택 정규화 모듈
    - 소문자 통일
    - 특수문자 제거
    - alias 매핑
    - 중복 제거
    """

    def __init__(self):
        # 대표 alias 테이블 (필요하면 계속 확장)
        self.alias_map: Dict[str, str] = {
            "js": "javascript",
            "ts": "typescript",
            "py": "python",
            "node": "nodejs",
            "node.js": "nodejs",
            "fast api": "fastapi",
            "fast-api": "fastapi",
            "react.js": "react",
            "reactjs": "react",
            "express.js": "express",
            "expressjs": "express",
            "c++": "cpp",
            "c#": "csharp",
            "ml": "machine learning",
            "ai": "artificial intelligence",
            "sklearn": "scikit-learn",
        }

        # 제거할 패턴 (버전, 괄호 등)
        self.clean_pattern = re.compile(r"[^a-z0-9+#. ]+")

    def _clean(self, skill: str) -> str:
        """
        기본 정리:
        - 소문자 변환
        - 특수문자 제거
        - 앞뒤 공백 제거
        """
        skill = skill.lower().strip()
        skill = self.clean_pattern.sub("", skill)
        skill = re.sub(r"\s+", " ", skill)
        return skill.strip()

    def _apply_alias(self, skill: str) -> str:
        """
        alias 변환
        """
        return self.alias_map.get(skill, skill)

    def normalize_one(self, skill: str) -> str:
        """
        단일 스킬 정규화
        """
        cleaned = self._clean(skill)
        return self._apply_alias(cleaned)

    def normalize_list(self, skills: List[str]) -> List[str]:
        """
        스킬 리스트 정규화 + 중복 제거
        """
        normalized_set: Set[str] = set()

        for skill in skills:
            if not skill:
                continue

            norm = self.normalize_one(skill)
            if norm:
                normalized_set.add(norm)

        return list(normalized_set)

    def normalize_text_blob(self, text: str) -> List[str]:
        """
        "Python, Java, Node.js" 같은 문자열 대응
        """
        if not text:
            return []

        # , / | 기준 분리
        raw_skills = re.split(r"[,\|/]", text)
        return self.normalize_list(raw_skills)


# ====== 싱글톤 사용 ======
skill_normalizer = SkillNormalizer()


# ====== 외부에서 쓰는 함수 ======
def normalize_skills(skills: List[str]) -> List[str]:
    return skill_normalizer.normalize_list(skills)


def normalize_skill_text(text: str) -> List[str]:
    return skill_normalizer.normalize_text_blob(text)