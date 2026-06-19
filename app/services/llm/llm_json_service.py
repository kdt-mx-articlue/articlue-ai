import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.utils.json_utils import extract_json_object


class LlmJsonService:
    def __init__(self):
        self.model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
        )

    def invoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        response = self.model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        return extract_json_object(str(response.content))