"""Simple chat service for sending queries to Anthropic Claude."""
import httpx
from anthropic import Anthropic
from src.config import Config


def chat(query: str, model: str = None, max_tokens: int = 1024) -> str:
    """
    Send a chat query to Anthropic Claude and get a response.
    
    Args:
        query: The user's question or message
        model: Claude model to use (defaults to Config.CLAUDE_MODEL)
        max_tokens: Maximum tokens in response (default 1024)
        
    Returns:
        The assistant's response text
        
    Example:
        >>> response = chat("What is Python?")
        >>> print(response)
    """
    # Create HTTP client with SSL verification disabled for corporate environments
    http_client = httpx.Client(verify=False, timeout=60.0)
    
    client = Anthropic(
        api_key=Config.ANTHROPIC_API_KEY,
        http_client=http_client
    )
    
    response = client.messages.create(
        model=model or Config.CLAUDE_MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "user", "content": query}
        ]
    )
    
    return response.content[0].text


def chat_with_history(messages: list, model: str = None, max_tokens: int = 1024, system: str = None) -> str:
    """
    Send a chat with conversation history to Anthropic Claude.
    
    Args:
        messages: List of message dicts [{"role": "user/assistant", "content": "..."}]
        model: Claude model to use (defaults to Config.CLAUDE_MODEL)
        max_tokens: Maximum tokens in response (default 1024)
        system: Optional system prompt
        
    Returns:
        The assistant's response text
        
    Example:
        >>> messages = [
        ...     {"role": "user", "content": "My name is John"},
        ...     {"role": "assistant", "content": "Hello John!"},
        ...     {"role": "user", "content": "What's my name?"}
        ... ]
        >>> response = chat_with_history(messages)
    """
    http_client = httpx.Client(verify=False, timeout=60.0)
    
    client = Anthropic(
        api_key=Config.ANTHROPIC_API_KEY,
        http_client=http_client
    )
    
    kwargs = {
        "model": model or Config.CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "messages": messages
    }
    
    if system:
        kwargs["system"] = system
    
    response = client.messages.create(**kwargs)
    
    return response.content[0].text


# Quick test
if __name__ == "__main__":
    response = chat("Say hello in one sentence.")
    print(f"Response: {response}")
