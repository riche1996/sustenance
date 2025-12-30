import httpx
from anthropic import Anthropic

ANTHROPIC_API_KEY="sk-ant-api03--*****************"
CLAUDE_MODEL="claude-sonnet-4-20250514"

def get_chat_completion(
    message: str,
    model: str = CLAUDE_MODEL,
    max_tokens: int = 50000) -> str:
    """
    Send a chat query to Anthropic Claude and get a response.
    """

    http_client = httpx.Client(
        verify=False,        # use only if corporate SSL interception
        timeout=60.0
    )

    client = Anthropic(
        api_key=ANTHROPIC_API_KEY,
        http_client=http_client
    )

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            }
        ]
    )

    return response.content[0].text