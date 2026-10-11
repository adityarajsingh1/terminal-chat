"""
Small wrappers around each provider's SDK so chat.py doesn't
have to care which one it's talking to. Each provider just needs
a .model attribute and a .stream(system, messages) generator.
"""

import os


class ClaudeProvider:
    default_model = "claude-sonnet-5-5"

    def __init__(self, model=None):
        import anthropic  # imported here so you only need the SDK you actually use

        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.client = anthropic.Anthropic()
        self.model = model or os.getenv("CLAUDE_MODEL", self.default_model)

    def stream(self, system, messages):
        with self.client.messages.stream(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text


class OpenAIProvider:
    default_model = "gpt-4o-mini"

    def __init__(self, model=None):
        from openai import OpenAI

        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.client = OpenAI()
        self.model = model or os.getenv("OPENAI_MODEL", self.default_model)

    def stream(self, system, messages):
        # openai wants the system prompt as the first message
        full = [{"role": "system", "content": system}] + messages
        response = self.client.chat.completions.create(
            model=self.model,
            messages=full,
            stream=True,
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class GeminiProvider:
    default_model = "gemini-2.5-flash"

    def __init__(self, model=None):
        from google import genai

        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("GEMINI_API_KEY is not set")
        self.client = genai.Client()
        self.model = model or os.getenv("GEMINI_MODEL", self.default_model)

    def stream(self, system, messages):
        from google.genai import types

        # gemini calls the assistant role "model" and wants the text wrapped in parts
        contents = [
            types.Content(role="model" if m["role"] == "assistant" else "user",
                          parts=[types.Part(text=m["content"])])
            for m in messages
        ]
        response = self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system),
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text


class OllamaProvider:
    """A model running on your own machine through Ollama. No API key, no cost, works offline."""

    default_model = "llama3.2"

    def __init__(self, model=None):
        import requests

        self.requests = requests
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", self.default_model)
        try:
            self.requests.get(f"{self.url}/api/tags", timeout=2).raise_for_status()
        except requests.RequestException:
            raise RuntimeError(f"can't reach Ollama at {self.url}. is it running? (`ollama serve`)")

    def stream(self, system, messages):
        import json

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}] + messages,
            "stream": True,
        }
        with self.requests.post(f"{self.url}/api/chat", json=payload, stream=True, timeout=300) as resp:
            resp.raise_for_status()
            # ollama streams one json object per line
            for line in resp.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if "error" in data:
                    raise RuntimeError(data["error"])
                yield data.get("message", {}).get("content", "")
                if data.get("done"):
                    break


PROVIDERS = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
}


def get_provider(name, model=None):
    return PROVIDERS[name](model)
