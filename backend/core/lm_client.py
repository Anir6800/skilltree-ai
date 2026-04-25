"""
LM Studio Client
Shared client for all AI-powered features in SkillTree AI.
Used by: executor, ai_evaluation, ai_detection, mentor apps.
"""

import requests
from typing import List, Dict, Any, Optional
from django.conf import settings


class ExecutionServiceUnavailable(Exception):
    """Raised when LM Studio service is unavailable or returns an error."""
    pass


class LMStudioClient:
    """
    Singleton client for LM Studio API interactions.
    Provides chat completion interface compatible with OpenAI API format.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.base_url = settings.LM_STUDIO_URL
        self.model = settings.LM_STUDIO_MODEL
        self.timeout = 30  # seconds
        self._initialized = True
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.1,
        response_format: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send chat completion request to LM Studio.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic)
            response_format: Optional format specification (e.g., {"type": "json_object"})
            
        Returns:
            Response dictionary with 'choices' containing generated text
            
        Raises:
            ExecutionServiceUnavailable: If service is down or returns error
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        endpoint = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise ExecutionServiceUnavailable(
                    f"LM Studio returned status {response.status_code}: {response.text}"
                )
            
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            raise ExecutionServiceUnavailable(
                f"Cannot connect to LM Studio at {self.base_url}. "
                f"Ensure LM Studio is running. Error: {str(e)}"
            )
        except requests.exceptions.Timeout:
            raise ExecutionServiceUnavailable(
                f"LM Studio request timed out after {self.timeout} seconds"
            )
        except requests.exceptions.RequestException as e:
            raise ExecutionServiceUnavailable(
                f"LM Studio request failed: {str(e)}"
            )
    
    def extract_content(self, response: Dict[str, Any]) -> str:
        """
        Extract text content from LM Studio response.
        
        Args:
            response: Response dictionary from chat_completion
            
        Returns:
            Generated text content
        """
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid response format from LM Studio: {e}")
    
    def is_available(self) -> bool:
        """
        Check if LM Studio service is available.
        
        Returns:
            True if service is reachable, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/models",
                timeout=5
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


# Singleton instance
lm_client = LMStudioClient()
