#!/usr/bin/env python3
"""
terminal-chat: a tiny chatbot that lives in your terminal.

Pick a provider (Claude or OpenAI), type messages, get answers.
The whole conversation is kept in memory so the model remembers
what you said earlier in the session.
"""

import argparse
import os
import sys

from providers import get_provider, PROVIDERS


HELP_TEXT = """commands:
  /help     show this
  /clear    forget the conversation so far
  /system   change the system prompt, e.g. /system you are a pirate
  /save     save the chat to a markdown file
  /quit     exit (ctrl+c works too)
"""


def save_chat(history, provider_name):
    # nothing fancy, just dump it as markdown so it's easy to read later
    filename = f"chat-{provider_name}.md"
    with open(filename, "w", encoding="utf-8") as f:
        for msg in history:
            who = "**me**" if msg["role"] == "user" else f"**{provider_name}**"
            f.write(f"{who}: {msg['content']}\n\n")
    return filename


def main():
    parser = argparse.ArgumentParser(description="Chat with an LLM from your terminal.")
    parser.add_argument("-p", "--provider", choices=PROVIDERS.keys(), default="claude",
                        help="which model provider to use (default: claude)")
    parser.add_argument("-m", "--model", help="override the default model name")
    parser.add_argument("-s", "--system", default="You are a helpful, concise assistant.",
                        help="system prompt")
    args = parser.parse_args()

    try:
        provider = get_provider(args.provider, args.model)
    except RuntimeError as e:
        print(f"error: {e}")
        sys.exit(1)

    system_prompt = args.system
    history = []

    print(f"chatting with {args.provider} ({provider.model}). type /help for commands.\n")

    while True:
        try:
            user_input = input("you > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nbye!")
            break

        if not user_input:
            continue

        # handle the slash commands first
        if user_input.startswith("/"):
            cmd, _, rest = user_input.partition(" ")
            if cmd == "/quit":
                print("bye!")
                break
            elif cmd == "/help":
                print(HELP_TEXT)
            elif cmd == "/clear":
                history.clear()
                print("(conversation cleared)\n")
            elif cmd == "/system":
                if rest:
                    system_prompt = rest
                    print("(system prompt updated)\n")
                else:
                    print(f"current system prompt: {system_prompt}\n")
            elif cmd == "/save":
                print(f"(saved to {save_chat(history, args.provider)})\n")
            else:
                print("unknown command, try /help\n")
            continue

        history.append({"role": "user", "content": user_input})

        print(f"{args.provider} > ", end="", flush=True)
        reply = ""
        try:
            # stream the answer so it shows up word by word instead of all at once
            for chunk in provider.stream(system_prompt, history):
                print(chunk, end="", flush=True)
                reply += chunk
        except Exception as e:
            print(f"\n[something went wrong: {e}]\n")
            history.pop()  # drop the message that failed so we can retry
            continue

        print("\n")
        history.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
