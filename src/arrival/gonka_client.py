# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
# AGPL-3.0-or-later

"""
Phase 16: Dual-Backend Inference Client

Supports two backends (same Qwen3-235B model):
  1. Gonka (primary)  — decentralized, ECDSA-signed, gonka-openai SDK
  2. OpenRouter (fallback) — standard OpenAI-compatible API

Backend selection via PHASE16_BACKEND env var or config_phase16.py.
Compatible interface with OpenRouterClient (LLMResponse dataclass).
"""

import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

# Fix Windows cp1251 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(errors='replace')

# Suppress verbose httpx/openai logging during normal operation
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("gonka").setLevel(logging.WARNING)

from openai import OpenAI, APIError, APITimeoutError, RateLimitError

from config_phase16 import (
    PHASE16_BACKEND,
    GONKA_PRIVATE_KEY, GONKA_SOURCE_URL, GONKA_MODEL_ID,
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL_ID,
    GONKA_MODEL_COSTS, GONKA_MODEL_SHORT,
    PHASE16_BUDGET_USD, PHASE16_ENABLE_THINKING,
    get_model_id,
)


@dataclass
class LLMResponse:
    """Extended response with cost and latency tracking.
    Same interface as openrouter_client.LLMResponse for pipeline compatibility."""
    text: str
    model: str
    provider: str = "gonka"
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
    """Raised when cumulative cost exceeds budget limit."""
    pass


class GonkaClient:
    """
    Dual-backend LLM client for Phase 16 experiments.

    Backend "gonka":     Uses GonkaOpenAI SDK (ECDSA-signed requests)
    Backend "openrouter": Uses standard OpenAI SDK with OpenRouter endpoint

    Both backends target the same model: Qwen3-235B-A22B.

    Usage:
        client = GonkaClient()  # auto-selects backend from config
        response = client.generate("Hello!")
        print(response.text, response.cost_usd)
    """

    def __init__(
        self,
        backend: Optional[str] = None,
        budget_limit: Optional[float] = None,
        verbose: bool = False,
    ):
        self.backend = backend or PHASE16_BACKEND
        self.model_id = get_model_id() if not backend else (
            GONKA_MODEL_ID if backend == "gonka" else OPENROUTER_MODEL_ID
        )
        self.budget_limit = budget_limit or PHASE16_BUDGET_USD
        self.cumulative_cost = 0.0
        self.total_calls = 0
        self.total_tokens = 0
        self.call_history: List[Dict[str, Any]] = []

        if verbose:
            logging.getLogger("httpx").setLevel(logging.INFO)
            logging.getLogger("gonka").setLevel(logging.INFO)

        # Initialize backend
        if self.backend == "gonka":
            self._init_gonka()
        else:
            self._init_openrouter()

    def _init_gonka(self):
        """Initialize Gonka decentralized backend with ECDSA signing."""
        if not GONKA_PRIVATE_KEY:
            raise EnvironmentError(
                "GONKA_PRIVATE_KEY required for Gonka backend. "
                "Get your key at https://gonka.ai/developer/quickstart/"
            )
        from gonka_openai import GonkaOpenAI
        self.client = GonkaOpenAI(
            gonka_private_key=GONKA_PRIVATE_KEY,
            source_url=GONKA_SOURCE_URL,
        )
        self.model_id = GONKA_MODEL_ID

    def _init_openrouter(self):
        """Initialize OpenRouter fallback backend."""
        api_key = OPENROUTER_API_KEY
        if not api_key:
            raise EnvironmentError(
                "OPENROUTER_API_KEY required for OpenRouter backend. "
                "Set it in .env or environment."
            )
        self.client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key,
        )
        self.model_id = OPENROUTER_MODEL_ID

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        max_retries: int = 3,
        enable_thinking: Optional[bool] = None,
    ) -> LLMResponse:
        """
        Send a prompt to Qwen3-235B via selected backend.

        Args:
            prompt: User message
            model: Model ID override (default: auto from backend)
            system_prompt: Optional system message
            max_tokens: Maximum response tokens
            temperature: Sampling temperature
            max_retries: Retry count on transient failures
            enable_thinking: Override thinking mode (None = use config default)

        Returns:
            LLMResponse with text, cost, latency, token counts
        """
        model = model or self.model_id

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

        # Thinking mode control
        thinking = enable_thinking if enable_thinking is not None else PHASE16_ENABLE_THINKING

        last_error = None
        for attempt in range(max_retries):
            try:
                start_time = time.time()

                # Build kwargs
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }

                # Disable thinking based on backend
                if not thinking:
                    if self.backend == "gonka":
                        # Gonka: extra_body for Qwen3 enable_thinking
                        kwargs["extra_body"] = {"enable_thinking": False}
                    else:
                        # OpenRouter: reasoning.effort = "none"
                        kwargs["extra_body"] = {"reasoning": {"effort": "none"}}

                response = self.client.chat.completions.create(**kwargs)
                latency_ms = (time.time() - start_time) * 1000

                # Extract text
                text = ""
                if response.choices:
                    message = response.choices[0].message
                    text = message.content or ""

                    # Strip any <think>...</think> blocks if they leaked through
                    if "<think>" in text:
                        text = re.sub(r'<think>.*?</think>\s*', '', text, flags=re.DOTALL)

                # Extract tokens
                prompt_tokens = 0
                completion_tokens = 0
                if response.usage:
                    prompt_tokens = response.usage.prompt_tokens or 0
                    completion_tokens = response.usage.completion_tokens or 0
                else:
                    prompt_tokens = self._estimate_tokens(
                        " ".join(m["content"] for m in messages)
                    )
                    completion_tokens = self._estimate_tokens(text)

                tokens_used = prompt_tokens + completion_tokens

                # Calculate cost
                cost = self._estimate_cost(model, prompt_tokens, completion_tokens)

                # Track
                self.cumulative_cost += cost
                self.total_calls += 1
                self.total_tokens += tokens_used

                finish_reason = ""
                if response.choices:
                    finish_reason = response.choices[0].finish_reason or ""

                result = LLMResponse(
                    text=text,
                    model=model,
                    provider=self.backend,
                    tokens_used=tokens_used,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    finish_reason=finish_reason,
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

            except RateLimitError as e:
                last_error = str(e)
                retry_after = 5
                print(f"  Rate limited, waiting {retry_after}s (attempt {attempt+1}/{max_retries})")
                time.sleep(retry_after)
                continue

            except APITimeoutError as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"  Timeout: {str(e)[:80]}. Retry in {wait}s...")
                    time.sleep(wait)
                continue

            except APIError as e:
                last_error = str(e)
                # On 402 Insufficient balance (Gonka), don't retry
                if '402' in str(e) and 'Insufficient balance' in str(e):
                    print(f"  402 Insufficient balance -- check Gonka account funding")
                    break
                # On 502 Bad Gateway, retry with delay
                if '502' in str(e):
                    if attempt < max_retries - 1:
                        wait = 5 * (attempt + 1)
                        print(f"  502 Bad Gateway. Retry in {wait}s...")
                        time.sleep(wait)
                    continue
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"  API Error: {str(e)[:80]}. Retry in {wait}s...")
                    time.sleep(wait)
                continue

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"  Error: {str(e)[:80]}. Retry in {wait}s...")
                    time.sleep(wait)
                continue

        # All retries exhausted
        return LLMResponse(
            text="",
            model=model,
            provider=self.backend,
            success=False,
            error=f"Failed after {max_retries} attempts: {last_error}",
        )

    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost based on known pricing."""
        pricing = GONKA_MODEL_COSTS.get(model, {"input": 0.70, "output": 2.80})
        cost = (
            (prompt_tokens / 1_000_000) * pricing["input"]
            + (completion_tokens / 1_000_000) * pricing["output"]
        )
        return round(cost, 6)

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation when usage is not returned.
        Approximation: 1 token ~ 4 chars for English text."""
        return max(1, len(text) // 4)

    def get_status(self) -> Dict[str, Any]:
        """Return current client status."""
        return {
            "backend": self.backend,
            "model": self.model_id,
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "cumulative_cost_usd": round(self.cumulative_cost, 4),
            "budget_remaining_usd": round(self.budget_limit - self.cumulative_cost, 4),
            "budget_limit_usd": self.budget_limit,
        }

    def get_model_short_name(self, model: str) -> str:
        """Get short display name for a model."""
        return GONKA_MODEL_SHORT.get(model, model.split("/")[-1])

    def test_connectivity(self) -> bool:
        """Test connectivity to selected backend. Returns True if successful."""
        print(f"  Testing {self.backend} API ({self.model_id})...", end=" ", flush=True)
        r = self.generate(
            "Respond with exactly: OK",
            model=self.model_id,
            max_tokens=10,
            temperature=0.0,
        )
        if r.success:
            print(f"OK ({r.latency_ms:.0f}ms, {r.tokens_used} tokens, ${r.cost_usd:.4f})")
        else:
            print(f"FAILED: {r.error[:120] if r.error else 'unknown error'}")
        return r.success
