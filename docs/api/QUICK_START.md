# OpenAI API - Quick Start

## Installation

```bash
# Install optional dependencies for token counting
pip install tiktoken

# Install OpenAI SDK for testing
pip install openai
```

## Start the Servers

```bash
# Terminal 1: Start Supervisor
python -m servers.supervisor_server

# Terminal 2: Start OpenAI-Compatible API
python -m servers.openai_compat_server
```

## Example 1: Simple Chat

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="cortex-flow",
    messages=[
        {"role": "user", "content": "What are AI agents?"}
    ]
)

print(response.choices[0].message.content)
print(f"Tokens used: {response.usage.total_tokens}")
```

## Example 2: Chatbot with Context

```python
from openai import OpenAI

class Chatbot:
    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:8001/v1",
            api_key="dummy"
        )
        self.messages = []
        self.conversation_id = None

    def send(self, user_input):
        # Add user message
        self.messages.append({
            "role": "user",
            "content": user_input
        })

        # Get response
        response = self.client.chat.completions.create(
            model="cortex-flow",
            messages=self.messages,
            conversation_id=self.conversation_id
        )

        # Store conversation ID
        if not self.conversation_id:
            self.conversation_id = response.conversation_id

        # Add assistant response
        assistant_message = response.choices[0].message.content
        self.messages.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

# Usage
bot = Chatbot()
print(bot.send("My name is Alice"))
print(bot.send("What is my name?"))  # Will remember "Alice"
```

## Example 3: Streaming

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="dummy"
)

print("Streaming response:")
stream = client.chat.completions.create(
    model="cortex-flow",
    messages=[
        {"role": "user", "content": "Write a short poem about AI"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

print("\n\nDone!")
```

## Example 4: Multi-Turn Conversation

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="dummy"
)

conversation_id = "research_session_1"

# Turn 1: Research request
response1 = client.chat.completions.create(
    model="cortex-flow",
    messages=[
        {"role": "user", "content": "Research the latest trends in AI agents"}
    ],
    conversation_id=conversation_id
)

print("Research Results:")
print(response1.choices[0].message.content)
print(f"\nAgents used: {response1.metadata.get('agents_used')}")
print()

# Turn 2: Follow-up analysis
response2 = client.chat.completions.create(
    model="cortex-flow",
    messages=[
        {"role": "user", "content": "Research the latest trends in AI agents"},
        {"role": "assistant", "content": response1.choices[0].message.content},
        {"role": "user", "content": "Analyze the key findings and trends"}
    ],
    conversation_id=conversation_id
)

print("Analysis:")
print(response2.choices[0].message.content)
print(f"\nAgents used: {response2.metadata.get('agents_used')}")
```

## Testing with curl

```bash
# Simple request
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "cortex-flow",
    "messages": [
      {"role": "user", "content": "Hello"}
    ]
  }'

# Streaming request
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "cortex-flow",
    "messages": [
      {"role": "user", "content": "Count to 5"}
    ],
    "stream": true
  }'

# List models
curl http://localhost:8001/v1/models
```

## Next Steps

- See [Full API Documentation](./openai_compatibility.md)
- Check [Example Applications](./examples/)
- Read about [Multi-Agent Architecture](../architecture/README.md)
