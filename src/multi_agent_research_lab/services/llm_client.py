import logging
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    content: Any
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client using OpenAI."""

    def __init__(self) -> None:
        settings = get_settings()
        # Initialize OpenAI client. Assumes OPENAI_API_KEY is in environment.
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def complete(
        self, system_prompt: str, user_prompt: str, response_format: type | None = None
    ) -> LLMResponse:
        """Return a model completion."""
        logger.debug(f"Calling LLM: {self.model}")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if response_format:
            # Requires openai>=1.40 for structured outputs
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,  # type: ignore
                response_format=response_format,
            )
            content = completion.choices[0].message.parsed  # This will be the pydantic object
            # For simplicity, if response_format is used, we return the parsed object in content,
            # but our signature expects str.
            # Let's adjust the signature to return Any for content or keep it str and serialize it.
            # Let's just return the raw string and let the caller parse it,
            # OR we can return the parsed object.
        else:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
            )
            content = completion.choices[0].message.content or ""

        usage = completion.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        # Simple cost calculation for gpt-4o-mini:
        # Input: $0.15 / 1M tokens
        # Output: $0.60 / 1M tokens
        cost_usd = None
        if "gpt-4o-mini" in self.model:
            cost_usd = (input_tokens / 1_000_000) * 0.15 + (output_tokens / 1_000_000) * 0.60

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )
