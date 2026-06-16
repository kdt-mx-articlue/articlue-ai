# app/services/vector/utils.py

def prepare_candidate_data(candidate_data: dict):

    def flatten_metadata(data: dict):

        flat = {}

        for k, v in data.items():

            # 기본 타입
            if isinstance(v, (str, int, float, bool)) or v is None:
                flat[k] = v

            # list → 문자열
            elif isinstance(v, list):
                flat[k] = ",".join(map(str, v))

            # dict → 문자열 (Chroma 금지 구조 제거)
            elif isinstance(v, dict):
                flat[k] = str(v)

            else:
                flat[k] = str(v)

        return flat

    return {
        "semantic_text": candidate_data.get("semantic_text", ""),

        "metadata": flatten_metadata(
            candidate_data.get("analysis_result", {})
        ),

        "resume_id": candidate_data.get("resume_id")
    }