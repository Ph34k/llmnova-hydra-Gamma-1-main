import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Optional

import anthropic
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

from ..interfaces.llm_provider import LLMProviderInterface, Message
from .redis_client import get_redis_client

logger = logging.getLogger(__name__)


class LLMProvider(LLMProviderInterface):
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.critic_model = "gpt-4o"

        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_client = None
        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def chat(
        self,
        history: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        temperature: float = 0.0
    ) -> Message:
        redis_client = get_redis_client()
        if not redis_client:
            # Proceed without cache if Redis is not available
            if self.model.startswith("claude-"):
                return self._chat_anthropic(history, tools, temperature)
            else:
                return self._chat_openai(history, tools, temperature)

        # Create a stable cache key
        cache_key_data = {
            "model": self.model,
            "history": history,
            "tools": tools,
            "temperature": temperature,
        }
        # Use json.dumps with sort_keys=True for a consistent hash
        serialized_data = json.dumps(cache_key_data, sort_keys=True)
        cache_key = f"llm_cache:{hashlib.sha256(serialized_data.encode('utf-8')).hexdigest()}"

        # Check for cached response
        cached_response = redis_client.get(cache_key)
        if cached_response:
            logger.info(f"Returning cached LLM response for key: {cache_key}")
            return Message.model_validate_json(cached_response)

        # If not cached, call the appropriate LLM
        if self.model.startswith("claude-"):
            response_message = self._chat_anthropic(history, tools, temperature)
        else:
            response_message = self._chat_openai(history, tools, temperature)

        # Cache the new response
        logger.info(f"Caching new LLM response for key: {cache_key}")
        redis_client.set(cache_key, response_message.model_dump_json(), ex=3600) # 1 hour TTL

        return response_message

    def _chat_openai(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0
    ) -> Message:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = self.openai_client.chat.completions.create(**kwargs)
            msg = response.choices[0].message
            return Message(
                role=msg.role,
                content=msg.content,
                tool_calls=msg.tool_calls if hasattr(msg, 'tool_calls') else None
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API Error: {e}") from e

    def _chat_anthropic(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0
    ) -> Message:
        if not self.anthropic_client:
            raise ValueError("Anthropic API Key not found but Claude model requested.")

        system_prompt = None
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append(msg)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": filtered_messages,
            "temperature": temperature,
            "max_tokens": 4096
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        if tools:
            kwargs["tools"] = tools

        try:
            response = self.anthropic_client.messages.create(**kwargs)

            content_text = ""
            tool_calls = []

            for block in response.content:
                if block.type == "text":
                    content_text += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": block.name,
                            "arguments": json.dumps(block.input)
                        }
                    })

            return Message(
                role="assistant",
                content=content_text,
                tool_calls=tool_calls if tool_calls else None
            )

        except Exception as e:
            raise RuntimeError(f"Anthropic API Error: {e}") from e

    def critique(self, code: str, goal: str) -> str:
        """Uses a separate context to critique code before execution."""
        prompt = [
            {"role": "system", "content": "You are a Senior Code Reviewer. Be harsh but constructive."},
            {"role": "user", "content": f"Review this code for the goal: '{goal}'.\n\nCODE:\n{code}\n\nList critical issues or return 'LGTM'."}
        ]
        
        if not self.openai_client:
            return "LGTM"

        response = self.openai_client.chat.completions.create(
            model=self.critic_model,
            messages=prompt,
            temperature=0.0
        )
        return response.choices[0].message.content or "LGTM"

