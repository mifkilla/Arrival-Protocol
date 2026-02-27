# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
ARRIVAL Phase 4: OpenRouter LLM Client
Single unified client for all models via OpenRouter API.
Replaces the multi-provider client from arrival_base/deus/llm/client.py
"""

import sys
import time
import requests
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

# Fix Windows cp1251 encoding — replace unencodable chars instead of crashing
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(errors='replace')

from arrival.config import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL,
    MODEL_COSTS, MODEL_SHORT, MAX_COST_USD,
    DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE,
)


@dataclass
class LLMResponse:
    """Extended response with cost and latency tracking."""
    text: str
    model: str
    provider: str = "openrouter"
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str = ""
    reasoning_content: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    latency_ms: float = 0.0
    cost_usd: float = 0.0


class BudgetExceededError(Exception):
    """Raised when cumulative cost exceeds MAX_COST_USD."""
    pass


class OpenRouterClient:
    """
    Unified LLM client via OpenRouter.

    Usage:
        client = OpenRouterClient()
        response = client.generate("Hello!", model="openai/gpt-4o")
        print(response.text, response.cost_usd)
    """

    def __init__(self, api_key: Optional[str] = None, budget_limit: Optional[float] = None):
        self.api_key = api_key or OPENROUTER_API_KEY
        if not self.api_key:
            raise EnvironmentError(
                "OPENROUTER_API_KEY environment variable is required. "
                "Get your key at https://openrouter.ai/keys"
            )
        self.base_url = OPENROUTER_BASE_URL
        self.budget_limit = budget_limit or MAX_COST_USD
        self.cumulative_cost = 0.0
        self.total_calls = 0
        self.total_tokens = 0
        self.call_history: List[Dict[str, Any]] = []

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/Methodiy-Kelevra/ARRIVAL",
            "X-Title": "ARRIVAL Protocol Phase 4",
            "Content-Type": "application/json",
        }

    def generate(
        self,
        prompt: str,
        model: str = "openai/gpt-4o",
        system_prompt: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        max_retries: int = 3,
    ) -> LLMResponse:
        """
        Send a prompt to a model via OpenRouter.

        Args:
            prompt: User message
            model: OpenRouter model ID (e.g., "openai/gpt-4o")
            system_prompt: Optional system message
            max_tokens: Maximum response tokens
            temperature: Sampling temperature
            max_retries: Retry count on transient failures

        Returns:
            LLMResponse with text, cost, latency, token counts
        """
        # Budget check
        if self.cumulative_cost >= self.budget_limit:
            raise BudgetExceededError(
                f"Budget limit ${self.budget_limit:.2f} exceeded. "
                f"Spent: ${self.cumulative_cost:.2f}"
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        last_error = None
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=120,
                )
                latency_ms = (time.time() - start_time) * 1000

                # Rate limit handling
                if response.status_code == 429:
                    retry_after = int(response.headers.get("retry-after", 5))
                    print(f"  ⏳ Rate limited, waiting {retry_after}s (attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                data = response.json()

                # Extract text
                text = ""
                choices = data.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    text = message.get("content", "")

                # Extract tokens
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                tokens_used = prompt_tokens + completion_tokens

                # Calculate cost
                cost = self._estimate_cost(model, prompt_tokens, completion_tokens)

                # Track
                self.cumulative_cost += cost
                self.total_calls += 1
                self.total_tokens += tokens_used

                result = LLMResponse(
                    text=text,
                    model=model,
                    provider="openrouter",
                    tokens_used=tokens_used,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    finish_reason=choices[0].get("finish_reason", "") if choices else "",
                    latency_ms=latency_ms,
                    cost_usd=cost,
                    success=True,
                )

                self.call_history.append({
                    "model": model,
                    "tokens": tokens_used,
                    "cost": cost,
                    "latency_ms": latency_ms,
                    "success": True,
                })

                return result

            except requests.exceptions.RequestException as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"  ⚠️ Error: {last_error[:80]}. Retry in {wait}s...")
                    time.sleep(wait)
                continue

        # All retries exhausted
        return LLMResponse(
            text="",
            model=model,
            provider="openrouter",
            success=False,
            error=f"Failed after {max_retries} attempts: {last_error}",
        )

    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost based on known pricing."""
        pricing = MODEL_COSTS.get(model, {"input": 1.0, "output": 3.0})
        cost = (
            (prompt_tokens / 1_000_000) * pricing["input"]
            + (completion_tokens / 1_000_000) * pricing["output"]
        )
        return round(cost, 6)

    def get_status(self) -> Dict[str, Any]:
        """Return current client status."""
        return {
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "cumulative_cost_usd": round(self.cumulative_cost, 4),
            "budget_remaining_usd": round(self.budget_limit - self.cumulative_cost, 4),
            "budget_limit_usd": self.budget_limit,
        }

    def get_model_short_name(self, model: str) -> str:
        """Get short display name for a model."""
        return MODEL_SHORT.get(model, model.split("/")[-1])

    def test_connectivity(self, models: Optional[List[str]] = None) -> Dict[str, bool]:
        """Test connectivity to each model. Returns {model: success}."""
        from config import MODELS
        test_models = models or list(MODELS.values())
        results = {}

        for model in test_models:
            short = self.get_model_short_name(model)
            print(f"  Testing {short}...", end=" ", flush=True)
            r = self.generate(
                "Respond with exactly: OK",
                model=model,
                max_tokens=10,
                temperature=0.0,
            )
            results[model] = r.success
            status = "✅" if r.success else f"❌ {r.error[:50]}"
            print(status)
            time.sleep(1)

        return results
