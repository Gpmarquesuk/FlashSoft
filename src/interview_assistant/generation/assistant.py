from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Iterable, Sequence

import requests


class GenerationError(Exception):
    pass


@dataclass
class GenerationConfig:
    model: str = "openai/gpt-4o-mini"
    max_tokens: int = 400
    temperature: float = 0.6


class InterviewResponseGenerator:
    def __init__(self, config: GenerationConfig | None = None, api_key: str | None = None) -> None:
        self.config = config or GenerationConfig()
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise GenerationError("OPENROUTER_API_KEY nao esta definido")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/GpmarquesUK/FlashSoft",
            "X-Title": "flashsoft-interview-assistant",
        }

    def build_prompt(
        self,
        question: str,
        resume_chunks: Sequence[str],
        jd_chunks: Sequence[str],
        transcript: Iterable[str],
    ) -> str:
        resume_section = "\n".join(resume_chunks[:20])
        jd_section = "\n".join(jd_chunks[:20])
        transcript_section = "\n".join(transcript)
        return (
            "You are a real-time interview coach."
            " Consider the current question, the resume highlights, the job description requirements, and the latest transcript snippets."
            " Reply in English with a confident, conversational tone and keep the final answer under 45 words."
            " Provide exactly three talking points, each no longer than 12 words, and reference the sources (resume, job description, recent experience)."
            " Respond strictly as JSON in the format:"
            ' {"final_answer": string, "talking_points": [string, ...], "sources": [string, ...]}.\n\n'
            f"Question: {question}\n\n"
            f"Resume snippets:\n{resume_section}\n\n"
            f"Job description snippets:\n{jd_section}\n\n"
            f"Recent transcript:\n{transcript_section}"
        )

    def generate(
        self,
        question: str,
        resume_chunks: Sequence[str],
        jd_chunks: Sequence[str],
        transcript: Iterable[str],
    ) -> dict:
        prompt = self.build_prompt(question, resume_chunks, jd_chunks, transcript)
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "You are an English-speaking interview coach focused on concise, accurate answers."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "response_format": {"type": "json_object"},
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=60,
        )
        if response.status_code >= 400:
            raise GenerationError(f"Model call failed: {response.status_code} {response.text}")
        data = response.json()["choices"][0]["message"]["content"]
        return _json_loads_safe(data)


def _json_loads_safe(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise GenerationError(f"Model response is not JSON: {exc}")
