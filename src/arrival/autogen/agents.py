# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

# ARRIVAL Protocol on AutoGen (AG2) — Agent Wrappers
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
AG2 ConversableAgent wrappers with ARRIVAL Protocol @-atom system prompts.
Uses OpenRouter API via OpenAI-compatible interface.
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from openai import OpenAI

try:
    from arrival.config import (
        ARRIVAL_SYSTEM_PROMPT,
        MCQ_SYSTEM_PROMPT_TEMPLATE,
        MODELS,
        OPENROUTER_API_KEY,
        OPENROUTER_BASE_URL,
        SABOTEUR_STRATEGIES,
        SABOTEUR_SYSTEM_PROMPT,
        get_llm_config,
    )
except ImportError:
    # AutoGen agents require Phase 4-era config names;
    # allow import for package discovery
    pass


class ARRIVALAgent:
    """
    Lightweight agent wrapper for ARRIVAL Protocol experiments.

    Uses direct OpenAI client (via OpenRouter) rather than AG2's
    ConversableAgent to maintain compatibility and simplicity.
    The AG2 framework is used for GroupChat orchestration.
    """

    def __init__(
        self,
        name: str,
        model_key: str,
        role: str = "honest",
        saboteur_strategy: Optional[str] = None,
    ):
        self.name = name
        self.model_key = model_key
        self.model_info = MODELS[model_key]
        self.role = role
        self.saboteur_strategy = saboteur_strategy
        self.messages: List[Dict] = []
        self.total_cost = 0.0
        self.total_tokens = 0

        self.client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )

    def build_system_prompt(
        self,
        question: Optional[Dict] = None,
        round_num: int = 1,
        role: str = "propose",
    ) -> str:
        """Build context-appropriate system prompt."""
        if self.role == "saboteur" and self.saboteur_strategy:
            strategy = SABOTEUR_STRATEGIES[self.saboteur_strategy]
            return SABOTEUR_SYSTEM_PROMPT.format(
                node_name=f"{self.model_info['name']}_{self.name}",
                strategy=strategy["name"],
                strategy_instructions=strategy["instructions"],
                attack_round=3,
            )

        if question:
            options_str = "\n".join(
                f"{k}) {v}" for k, v in question["options"].items()
            )
            return MCQ_SYSTEM_PROMPT_TEMPLATE.format(
                node_name=f"{self.model_info['name']}_{self.name}",
                arrival_atoms=ARRIVAL_SYSTEM_PROMPT,
                question=question["question"],
                options=options_str,
                round_num=round_num,
                role=role,
            )

        return ARRIVAL_SYSTEM_PROMPT.replace(
            "You are a node",
            f"You are {self.model_info['name']}_{self.name}, a node",
        )

    def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
    ) -> Tuple[str, float]:
        """
        Send a message and get response.

        Returns:
            (response_text, cost)
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        for msg in self.messages:
            messages.append(msg)

        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.model_info["model"],
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
                extra_headers={
                    "HTTP-Referer": "https://github.com/arrival-protocol",
                    "X-Title": "ARRIVAL Protocol AutoGen Experiments",
                },
            )

            content = response.choices[0].message.content or ""
            usage = response.usage

            # Estimate cost (approximate OpenRouter pricing)
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            # Rough estimate: $0.20/M input, $0.60/M output for open models
            cost = (prompt_tokens * 0.20 + completion_tokens * 0.60) / 1_000_000
            self.total_cost += cost
            self.total_tokens += (prompt_tokens + completion_tokens)

            # Track conversation
            self.messages.append({"role": "user", "content": user_message})
            self.messages.append({"role": "assistant", "content": content})

            time.sleep(1)  # Rate limiting
            return content, cost

        except Exception as e:
            print(f"  [ERROR] {self.name}: {e}")
            return f"[ERROR: {e}]", 0.0

    def reset(self):
        """Reset conversation history."""
        self.messages = []


class ARRIVALGroupChat:
    """
    Manages a group of ARRIVAL agents in structured dialogue.

    This replaces AG2's GroupChat with a simpler, more controllable
    implementation that follows the ARRIVAL Protocol round structure.
    """

    def __init__(self, agents: List[ARRIVALAgent], rounds: int = 4):
        self.agents = agents
        self.rounds = rounds
        self.transcript: List[Dict] = []
        self.total_cost = 0.0

    def run_mcq(self, question: Dict) -> Dict:
        """
        Run MCQ consensus dialogue.

        Round structure:
        1. Agent 0: Propose (analyze and suggest answer)
        2. Agent 1: Respond (agree/disagree, provide own analysis)
        3. Agent 2: Synthesize (review both, propose resolution)
        4. Agent 0: Finalize (declare consensus)

        Returns:
            Dict with full results and metrics.
        """
        roles = ["propose", "respond", "synthesize", "finalize"]
        agent_order = [0, 1, 2, 0]  # Who speaks in each round

        context = ""
        self.transcript = []

        for round_num in range(1, self.rounds + 1):
            agent_idx = agent_order[round_num - 1]
            agent = self.agents[agent_idx]
            role = roles[round_num - 1]

            system_prompt = agent.build_system_prompt(
                question=question,
                round_num=round_num,
                role=role,
            )

            if round_num == 1:
                user_msg = (
                    f"Begin Round {round_num}. "
                    f"You are the first to analyze this question. "
                    f"Propose your answer using @-atoms."
                )
            else:
                user_msg = (
                    f"Round {round_num}. Previous discussion:\n\n"
                    f"{context}\n\n"
                    f"Your role: {role}. Respond using @-atoms."
                )

            response, cost = agent.chat(user_msg, system_prompt)
            self.total_cost += cost

            entry = {
                "round": round_num,
                "from": agent.name,
                "model": agent.model_key,
                "role": role,
                "message": response,
                "cost": cost,
            }
            self.transcript.append(entry)

            # Build context for next round
            context += (
                f"\n--- Round {round_num} ({agent.model_info['name']}, "
                f"role: {role}) ---\n{response}\n"
            )

            print(
                f"  Round {round_num}/{self.rounds}: "
                f"{agent.model_info['short']} ({role}) "
                f"[{len(response)} chars, ${cost:.4f}]"
            )

        # Reset agents for next question
        for agent in self.agents:
            agent.reset()

        return {
            "question_id": question["id"],
            "question": question["question"],
            "correct_answer": question["correct"],
            "transcript": self.transcript,
            "total_cost": self.total_cost,
        }

    def run_adversarial_mcq(
        self,
        question: Dict,
        saboteur_idx: int = 3,
        rounds: int = 6,
    ) -> Dict:
        """
        Run adversarial MCQ dialogue with saboteur injected.

        Rounds 1-2: Normal dialogue (honest agents)
        Round 3: Saboteur speaks
        Rounds 4-6: Remaining agents respond and finalize

        Returns:
            Dict with full results including adversarial metrics.
        """
        context = ""
        self.transcript = []
        self.total_cost = 0.0

        # Agent speaking order: honest agents rotate, saboteur at round 3
        honest_agents = [a for a in self.agents if a.role != "saboteur"]
        saboteur = self.agents[saboteur_idx] if saboteur_idx < len(self.agents) else None

        speaker_order = [
            honest_agents[0],   # Round 1: propose
            honest_agents[1],   # Round 2: respond
            saboteur or honest_agents[2],  # Round 3: saboteur/synthesize
            honest_agents[2] if saboteur else honest_agents[0],  # Round 4
            honest_agents[0],   # Round 5
            honest_agents[1],   # Round 6: finalize
        ]

        roles = ["propose", "respond", "attack", "evaluate", "synthesize", "finalize"]

        for round_num in range(1, rounds + 1):
            if round_num > len(speaker_order):
                break

            agent = speaker_order[round_num - 1]
            role = roles[round_num - 1]

            system_prompt = agent.build_system_prompt(
                question=question,
                round_num=round_num,
                role=role,
            )

            if round_num == 1:
                user_msg = (
                    f"Begin Round {round_num}. "
                    f"Analyze this question and propose your answer using @-atoms."
                )
            else:
                user_msg = (
                    f"Round {round_num}. Previous discussion:\n\n"
                    f"{context}\n\n"
                    f"Respond using @-atoms."
                )

            response, cost = agent.chat(user_msg, system_prompt)
            self.total_cost += cost

            entry = {
                "round": round_num,
                "from": agent.name,
                "model": agent.model_key,
                "role": role,
                "is_saboteur": agent.role == "saboteur",
                "message": response,
                "cost": cost,
            }
            self.transcript.append(entry)

            context += (
                f"\n--- Round {round_num} ({agent.model_info['name']}) ---\n"
                f"{response}\n"
            )

            marker = " [SABOTEUR]" if agent.role == "saboteur" else ""
            print(
                f"  Round {round_num}/{rounds}: "
                f"{agent.model_info['short']} ({role}){marker} "
                f"[{len(response)} chars, ${cost:.4f}]"
            )

        for agent in self.agents:
            agent.reset()

        return {
            "question_id": question["id"],
            "question": question["question"],
            "correct_answer": question["correct"],
            "saboteur_strategy": (
                saboteur.saboteur_strategy if saboteur else None
            ),
            "transcript": self.transcript,
            "total_cost": self.total_cost,
        }
