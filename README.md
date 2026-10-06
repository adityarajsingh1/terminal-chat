# terminal-chat 💬

A small chatbot that runs in your terminal and can talk to **Claude**, **OpenAI** or **Gemini** models.

I wanted a quick way to try out different LLMs side by side without opening a bunch of browser tabs, so I put this together. It's intentionally small (two Python files) so it's easy to read and hack on.

## What it does

- chat with Claude, GPT or Gemini from the command line
- responses stream in as they're generated
- remembers the conversation during a session
- a few handy commands: `/clear`, `/system`, `/save`, `/help`, `/quit`

## Setup

You'll need Python 3.9+ and an API key for at least one provider.

```bash
git clone https://github.com/adityarajsingh1/terminal-chat.git
cd terminal-chat
python -m venv .venv
source .venv/bin/activate      # on windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Then set your key(s):

```bash
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
export GEMINI_API_KEY="your-key-here"   # free key from Google AI Studio
```

You only need the key for the provider you're going to use.

## Usage

```bash
# default is claude
python chat.py

# use openai instead
python chat.py --provider openai

# or gemini
python chat.py -p gemini

# pick a specific model
python chat.py -p openai -m gpt-4o

# give it a personality
python chat.py --system "You are a grumpy but helpful senior engineer."
```

Example:

```
chatting with claude (claude-sonnet-5-5). type /help for commands.

you > explain recursion in one sentence
claude > Recursion is when a function solves a problem by calling itself on a smaller version of the same problem until it hits a case simple enough to answer directly.
```

## How it's structured

- `chat.py` - the loop that reads your input, handles commands and prints replies
- `providers.py` - one small class per provider. Adding a new one (Gemini, Mistral, a local model...) just means writing another class with a `stream()` method and adding it to `PROVIDERS`

## Things I'd like to add

- [x] Gemini
- [ ] a local model through Ollama
- [ ] ask both models the same question and show answers side by side
- [ ] remember chats between sessions
- [ ] show token usage / rough cost per message

Feel free to fork it and play around.
