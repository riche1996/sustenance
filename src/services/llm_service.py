"""LLM Service abstraction layer for multiple providers (Azure OpenAI, Anthropic Claude)."""
import logging
import httpx
from typing import Optional, Generator, List, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], 
                       max_tokens: int = 4096,
                       temperature: float = 0.7,
                       system: str = None) -> Dict[str, Any]:
        """Get a chat completion response. Returns dict with 'content' key."""
        pass
    
    @abstractmethod
    def chat_completion_stream(self, messages: List[Dict[str, str]], 
                               max_tokens: int = 4096,
                               temperature: float = 0.7) -> Generator[str, None, None]:
        """Get a streaming chat completion response."""
        pass


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI LLM provider."""
    
    def __init__(self, endpoint: str, api_key: str, deployment: str, 
                 api_version: str = "2024-02-15-preview"):
        """
        Initialize Azure OpenAI provider.
        
        Args:
            endpoint: Azure OpenAI endpoint URL (base URL or full URL)
            api_key: Azure OpenAI API key
            deployment: Deployment name (model)
            api_version: API version
        """
        # Check if endpoint is a full URL (contains /openai/deployments/)
        if "/openai/deployments/" in endpoint:
            # Use endpoint as-is (it's a full URL)
            self.full_url = endpoint.rstrip('/')
            self.is_full_url = True
        else:
            # Base URL - we'll construct the full path
            self.endpoint = endpoint.rstrip('/')
            self.is_full_url = False
        
        self.api_key = api_key
        self.deployment = deployment
        self.api_version = api_version
        
        # Create HTTP client with SSL verification disabled for corporate environments
        self.http_client = httpx.Client(
            verify=False,
            timeout=120.0
        )
        
        # Retry settings for rate limiting
        self.max_retries = 3
        self.base_delay = 2  # seconds
        
        logger.info(f"Azure OpenAI provider initialized (deployment: {deployment})")
    
    def _get_api_url(self) -> str:
        """Get the API URL for chat completions."""
        if self.is_full_url:
            return self.full_url
        return f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"
    
    def _make_request_with_retry(self, url: str, headers: Dict, json_data: Dict, 
                                  stream: bool = False) -> Any:
        """Make HTTP request with retry logic for rate limiting."""
        import time
        
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                if stream:
                    return self.http_client.stream("POST", url, headers=headers, json=json_data)
                else:
                    response = self.http_client.post(url, headers=headers, json=json_data)
                    
                    # Check for rate limiting
                    if response.status_code == 429:
                        retry_after = response.headers.get('Retry-After', self.base_delay * (2 ** attempt))
                        try:
                            wait_time = int(retry_after)
                        except (ValueError, TypeError):
                            wait_time = self.base_delay * (2 ** attempt)
                        
                        if attempt < self.max_retries:
                            logger.warning(f"Rate limited (429). Retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})")
                            time.sleep(wait_time)
                            continue
                    
                    response.raise_for_status()
                    return response
                    
            except Exception as e:
                last_error = e
                if "429" in str(e) and attempt < self.max_retries:
                    wait_time = self.base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited. Retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue
                raise
        
        raise last_error or Exception("Max retries exceeded")
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       max_tokens: int = 4096,
                       temperature: float = 0.7,
                       system: str = None) -> Dict[str, Any]:
        """
        Get a chat completion response from Azure OpenAI.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            system: Optional system prompt
            
        Returns:
            Dict with 'content' key containing response text
        """
        try:
            # Add system message if provided
            all_messages = messages.copy()
            if system:
                all_messages.insert(0, {"role": "system", "content": system})
            
            response = self._make_request_with_retry(
                self._get_api_url(),
                headers={
                    "Content-Type": "application/json",
                    "api-key": self.api_key
                },
                json_data={
                    "messages": all_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            result = response.json()
            return {"content": result["choices"][0]["message"]["content"]}
            
        except Exception as e:
            logger.error(f"Azure OpenAI error: {e}")
            raise
    
    def chat_completion_stream(self, messages: List[Dict[str, str]], 
                               max_tokens: int = 4096,
                               temperature: float = 0.7) -> Generator[str, None, None]:
        """
        Get a streaming chat completion response from Azure OpenAI.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Yields:
            Response text chunks
        """
        import json
        import time
        
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                with self.http_client.stream(
                    "POST",
                    self._get_api_url(),
                    headers={
                        "Content-Type": "application/json",
                        "api-key": self.api_key
                    },
                    json={
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": True
                    }
                ) as response:
                    # Check for rate limiting before processing
                    if response.status_code == 429:
                        retry_after = response.headers.get('Retry-After', self.base_delay * (2 ** attempt))
                        try:
                            wait_time = int(retry_after)
                        except (ValueError, TypeError):
                            wait_time = self.base_delay * (2 ** attempt)
                        
                        if attempt < self.max_retries:
                            logger.warning(f"Rate limited (429). Retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})")
                            time.sleep(wait_time)
                            continue
                    
                    response.raise_for_status()
                    
                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if chunk["choices"] and chunk["choices"][0].get("delta", {}).get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except json.JSONDecodeError:
                                continue
                    return  # Success, exit retry loop
                    
            except Exception as e:
                last_error = e
                if "429" in str(e) and attempt < self.max_retries:
                    wait_time = self.base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited. Retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue
                logger.error(f"Azure OpenAI streaming error: {e}")
                raise
        
        if last_error:
            raise last_error


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Anthropic Claude provider.
        
        Args:
            api_key: Anthropic API key
            model: Model name
        """
        self.api_key = api_key
        self.model = model
        self._client = None
        
        logger.info(f"Anthropic provider initialized (model: {model})")
    
    def _get_client(self):
        """Lazy load Anthropic client."""
        if self._client is None:
            from anthropic import Anthropic
            
            http_client = httpx.Client(
                verify=False,
                timeout=120.0
            )
            
            self._client = Anthropic(
                api_key=self.api_key,
                http_client=http_client
            )
        return self._client
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple:
        """
        Convert OpenAI-style messages to Anthropic format.
        
        Returns:
            Tuple of (system_prompt, messages_list)
        """
        system_prompt = ""
        anthropic_messages = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                anthropic_messages.append({"role": "user", "content": content})
            elif role == "assistant":
                anthropic_messages.append({"role": "assistant", "content": content})
        
        return system_prompt, anthropic_messages
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       max_tokens: int = 4096,
                       temperature: float = 0.7,
                       system: str = None) -> Dict[str, Any]:
        """
        Get a chat completion response from Anthropic Claude.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            system: Optional system prompt (overrides system in messages)
            
        Returns:
            Dict with 'content' key containing response text
        """
        try:
            client = self._get_client()
            system_prompt, anthropic_messages = self._convert_messages(messages)
            
            # Use explicit system param if provided
            if system:
                system_prompt = system
            
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": anthropic_messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = client.messages.create(**kwargs)
            return {"content": response.content[0].text}
            
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            raise
    
    def chat_completion_stream(self, messages: List[Dict[str, str]], 
                               max_tokens: int = 4096,
                               temperature: float = 0.7) -> Generator[str, None, None]:
        """
        Get a streaming chat completion response from Anthropic Claude.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Yields:
            Response text chunks
        """
        try:
            client = self._get_client()
            system_prompt, anthropic_messages = self._convert_messages(messages)
            
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": anthropic_messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            with client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise


class LLMService:
    """
    LLM Service that provides access to different LLM providers.
    
    Supports:
    - Azure OpenAI (for agent routing/chat)
    - Anthropic Claude (for code analysis)
    """
    
    _agent_provider: Optional[BaseLLMProvider] = None
    _code_analysis_provider: Optional[BaseLLMProvider] = None
    
    @classmethod
    def get_agent_provider(cls) -> BaseLLMProvider:
        """
        Get the LLM provider for agent routing and chat.
        
        Returns:
            LLM provider instance
        """
        if cls._agent_provider is None:
            from src.config import Config
            
            provider_type = Config.AGENT_LLM_PROVIDER.lower()
            
            if provider_type == "azure":
                cls._agent_provider = AzureOpenAIProvider(
                    endpoint=Config.AZURE_OPENAI_ENDPOINT,
                    api_key=Config.AZURE_OPENAI_KEY,
                    deployment=Config.AZURE_OPENAI_DEPLOYMENT,
                    api_version=Config.AZURE_OPENAI_API_VERSION
                )
                print(f"🤖 Agent LLM: Azure OpenAI ({Config.AZURE_OPENAI_DEPLOYMENT})")
            else:
                # Default to Anthropic
                cls._agent_provider = AnthropicProvider(
                    api_key=Config.ANTHROPIC_API_KEY,
                    model=Config.CLAUDE_MODEL
                )
                print(f"🤖 Agent LLM: Anthropic Claude ({Config.CLAUDE_MODEL})")
        
        return cls._agent_provider
    
    @classmethod
    def get_code_analysis_provider(cls) -> BaseLLMProvider:
        """
        Get the LLM provider for code analysis.
        Always uses Claude for best code understanding.
        
        Returns:
            LLM provider instance
        """
        if cls._code_analysis_provider is None:
            from src.config import Config
            
            provider_type = Config.CODE_ANALYSIS_LLM.lower()
            
            if provider_type == "azure":
                cls._code_analysis_provider = AzureOpenAIProvider(
                    endpoint=Config.AZURE_OPENAI_ENDPOINT,
                    api_key=Config.AZURE_OPENAI_KEY,
                    deployment=Config.AZURE_OPENAI_DEPLOYMENT,
                    api_version=Config.AZURE_OPENAI_API_VERSION
                )
                print(f"🔍 Code Analysis LLM: Azure OpenAI ({Config.AZURE_OPENAI_DEPLOYMENT})")
            else:
                # Default to Anthropic (Claude is best for code)
                cls._code_analysis_provider = AnthropicProvider(
                    api_key=Config.ANTHROPIC_API_KEY,
                    model=Config.CLAUDE_MODEL
                )
                print(f"🔍 Code Analysis LLM: Anthropic Claude ({Config.CLAUDE_MODEL})")
        
        return cls._code_analysis_provider
    
    @classmethod
    def reset(cls):
        """Reset providers (useful for testing or config changes)."""
        cls._agent_provider = None
        cls._code_analysis_provider = None


# Convenience functions for easy access
def get_agent_llm() -> BaseLLMProvider:
    """Get the agent LLM provider."""
    return LLMService.get_agent_provider()


def get_code_analysis_llm() -> BaseLLMProvider:
    """Get the code analysis LLM provider."""
    return LLMService.get_code_analysis_provider()
