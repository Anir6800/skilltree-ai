"""
LM Studio Client
Shared client for all AI-powered features in SkillTree AI.
Used by: executor, ai_evaluation, ai_detection, mentor apps.
"""

import time
import logging
import requests
from typing import List, Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class ExecutionServiceUnavailable(Exception):
    """Raised when LM Studio service is unavailable or returns an error."""
    pass


class LMStudioClient:
    """
    Singleton client for LM Studio API interactions.
    Provides chat completion interface compatible with OpenAI API format.

    Availability is cached for LM_STUDIO_AVAILABILITY_CACHE_TTL seconds
    (default 30s) to prevent hammering LM Studio with health-check requests
    from every Celery task / Django request, which was the root cause of the
    LM Studio restart loop.
    """

    _instance = None

    # ── Availability cache ────────────────────────────────────────────────────
    # Caches the result of is_available() so we don't hit LM Studio on every
    # single AI call.  Configurable via settings.LM_STUDIO_AVAILABILITY_CACHE_TTL
    _availability_cache: Optional[bool] = None
    _availability_cache_ts: float = 0.0
    _AVAILABILITY_CACHE_TTL: float = 30.0  # seconds

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
        self.timeout = getattr(settings, 'LM_STUDIO_TIMEOUT', 30)  # seconds
        self._AVAILABILITY_CACHE_TTL = float(
            getattr(settings, 'LM_STUDIO_AVAILABILITY_CACHE_TTL', 30)
        )
        self._initialized = True

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.1,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Send chat completion request to LM Studio.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic)
            response_format: Optional format specification

        Returns:
            Response dictionary with 'choices' containing generated text

        Raises:
            ExecutionServiceUnavailable: If service is down or returns error
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")

        endpoint = f"{self.base_url}/chat/completions"

        payload: Dict[str, Any] = {
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
                headers={"Content-Type": "application/json"},
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

        Result is cached for _AVAILABILITY_CACHE_TTL seconds to prevent
        hammering LM Studio with repeated health-check requests (which was
        the root cause of the restart loop).

        Returns:
            True if service is reachable, False otherwise
        """
        now = time.monotonic()
        if (
            self._availability_cache is not None
            and (now - self._availability_cache_ts) < self._AVAILABILITY_CACHE_TTL
        ):
            return self._availability_cache

        try:
            response = requests.get(
                f"{self.base_url}/models",
                timeout=5,
            )
            result = response.status_code == 200
        except requests.exceptions.RequestException:
            result = False

        # Update cache
        LMStudioClient._availability_cache = result
        LMStudioClient._availability_cache_ts = now

        if not result:
            logger.warning(
                "LM Studio is not available at %s. "
                "AI features will use fallback responses. "
                "Next availability check in %.0fs.",
                self.base_url,
                self._AVAILABILITY_CACHE_TTL,
            )

        return result

    def invalidate_availability_cache(self) -> None:
        """Force the next is_available() call to re-check LM Studio."""
        LMStudioClient._availability_cache = None
        LMStudioClient._availability_cache_ts = 0.0


# Singleton instance
lm_client = LMStudioClient()
