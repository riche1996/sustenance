"""Simple chat service using LLM service abstraction."""
from src.services.llm_service import get_agent_llm


def chat(query: str, model: str = None, max_tokens: int = 1024) -> str:
    """
    Send a chat query to the configured agent LLM and get a response.
    
    Args:
        query: The user's question or message
        model: Model to use (optional, uses default from config)
        max_tokens: Maximum tokens in response (default 1024)
        
    Returns:
        The assistant's response text
        
    Example:
        >>> response = chat("What is Python?")
        >>> print(response)
    """
    llm_provider = get_agent_llm()
    
    result = llm_provider.chat_completion(
        messages=[
            {"role": "user", "content": query}
        ],
        max_tokens=max_tokens
    )
    
    return result.get("content", "")


def chat_with_history(messages: list, model: str = None, max_tokens: int = 1024, system: str = None) -> str:
    """
    Send a chat with conversation history to the configured agent LLM.
    
    Args:
        messages: List of message dicts [{"role": "user/assistant", "content": "..."}]
        model: Model to use (optional, uses default from config)
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
    llm_provider = get_agent_llm()
    
    result = llm_provider.chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        system=system
    )
    
    return result.get("content", "")


# Quick test
if __name__ == "__main__":
    response = chat("Say hello in one sentence.")
    print(f"Response: {response}")
