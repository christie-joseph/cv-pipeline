import os
from typing import List
from openai import OpenAI
from .base import BaseRewriter


class ApiRewriter(BaseRewriter):
    def __init__(self, api_url: str, api_model: str, timeout_seconds: int = 5):
        self.api_url = api_url
        self.api_model = api_model
        self.timeout_seconds = timeout_seconds
        self.api_key = os.getenv("LLM_API_KEY")
        self.client = None

        if self.api_key and len(self.api_key.strip()) > 0:
            self.client = OpenAI(
                api_key=self.api_key.strip(),
                base_url=self.api_url,
                timeout=float(self.timeout_seconds)
            )

    def is_available(self) -> bool:
        return self.client is not None

    def rewrite(self, bullet_text: str, jd_keywords: List[str], prompt_template: str) -> str:
        if not self.is_available():
            raise RuntimeError("Cloud LLM API key not configured.")

        keywords_str = ", ".join(jd_keywords[:10])
        user_prompt = (
            f"Original Bullet: {bullet_text}\n"
            f"Target Job Keywords: {keywords_str}\n\n"
            f"Instructions:\n{prompt_template}"
        )

        response = self.client.chat.completions.create(
            model=self.api_model,
            messages=[
                {"role": "system", "content": "You are a professional resume tailoring assistant."},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )

        content = response.choices[0].message.content
        if content:
            return content.strip().strip('"')
        return bullet_text
