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
        tool_choice: Optional[Any] = None,
        temperature: float = 0.0
    ) -> Message:
        redis_client = get_redis_client()
        if not redis_client:
            # Proceed without cache if Redis is not available
            if self.model.startswith("claude-"):
                return self._chat_anthropic(history, tools, tool_choice, temperature)
            else:
                return self._chat_openai(history, tools, tool_choice, temperature)

        # Create a stable cache key
        cache_key_data = {
            "model": self.model,
            "history": history,
            "tools": tools,
            "tool_choice": tool_choice,
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
            response_message = self._chat_anthropic(history, tools, tool_choice, temperature)
        else:
            response_message = self._chat_openai(history, tools, tool_choice, temperature)

        # Cache the new response
        logger.info(f"Caching new LLM response for key: {cache_key}")
        redis_client.set(cache_key, response_message.model_dump_json(), ex=3600) # 1 hour TTL

        return response_message

    def _chat_openai(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        temperature: float = 0.0
    ) -> Message:
        # Pre-process messages for image support
        formatted_messages = []
        for msg in messages:
            new_msg = {"role": msg["role"]}

            # If base64_image is present, format content as list
            if msg.get("base64_image"):
                content_list = []
                if msg.get("content"):
                    content_list.append({"type": "text", "text": msg["content"]})

                content_list.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{msg['base64_image']}"
                    }
                })
                new_msg["content"] = content_list
            else:
                new_msg["content"] = msg.get("content")

            # Copy other fields if necessary (tool_calls, etc.)
            if msg.get("tool_calls"):
                new_msg["tool_calls"] = msg["tool_calls"]
            if msg.get("tool_call_id"):
                new_msg["tool_call_id"] = msg["tool_call_id"]
            if msg.get("name"):
                new_msg["name"] = msg["name"]

            formatted_messages.append(new_msg)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice if tool_choice else "auto"

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
        tool_choice: Optional[Any] = None,
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
                # Format for Anthropic images
                new_msg = {"role": msg["role"]}
                if msg.get("base64_image"):
                    content_list = []
                    if msg.get("content"):
                        content_list.append({"type": "text", "text": msg["content"]})

                    content_list.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": msg["base64_image"]
                        }
                    })
                    new_msg["content"] = content_list
                else:
                    new_msg["content"] = msg.get("content")

                # Copy tool related fields if needed? Anthropic handles tool use differently in history
                # Usually assistant messages with tool_use blocks are handled by 'content' being a list
                # This simple adapter might need more robust history conversion for tools, but for images this works.

                filtered_messages.append(new_msg)

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
            # Basic mapping for Anthropic tool_choice if needed
            if tool_choice:
                 # OpenAI 'auto' maps to Anthropic default (omitted or auto)
                 # OpenAI 'required' (not supported directly in basic generic way without more logic)
                 # OpenAI 'none' -> don't send tools?
                 if tool_choice != "auto":
                     # For now, simplistic handling. Full support requires more complex mapping.
                     pass

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

