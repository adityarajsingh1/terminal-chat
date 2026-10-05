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


PROVIDERS = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
}


def get_provider(name, model=None):
    return PROVIDERS[name](model)
