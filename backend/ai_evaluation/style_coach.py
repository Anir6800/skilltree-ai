"""
SkillTree AI - Code Style Coach
AI-powered code style analysis using LM Studio.
Runs after quest passes to provide style, readability, and idiom feedback.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.core.cache import cache
from core.lm_client import lm_client, ExecutionServiceUnavailable
from quests.models import QuestSubmission, Quest

logger = logging.getLogger(__name__)

STYLE_CACHE_TTL = 3600


class CodeStyleCoach:
    """
    Analyzes code style, readability, and idiomatic patterns.
    Only runs after quest is PASSED — correctness must come first.
    """

    def __init__(self):
        """Initialize style coach with LM Studio client."""
        self.client = lm_client
        self.cache_ttl = STYLE_CACHE_TTL

    def analyse_style(self, code: str, language: str, quest: Quest) -> Dict[str, Any]:
        """
        Analyze code style, readability, and idiomatic patterns.

        Args:
            code: Source code to analyze
            language: Programming language (python, javascript, cpp, java, go)
            quest: Quest object for context

        Returns:
            Dictionary with:
            - readability_score: 0-10 score
            - naming_quality: Assessment of naming
            - style_issues: List of issues with suggestions
            - positive_patterns: List of things done well

        Raises:
            ValueError: If language not supported
            ExecutionServiceUnavailable: If LM Studio unavailable
        """
        if language not in ['python', 'javascript', 'cpp', 'java', 'go']:
            raise ValueError(f"Unsupported language: {language}")

        if not code or len(code.strip()) == 0:
            raise ValueError("Code cannot be empty")

        cache_key = self._get_cache_key(code, language, quest.id)
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Style analysis cache hit for quest {quest.id}")
            return cached_result

        try:
            system_prompt = self._build_system_prompt(language)
            user_prompt = self._build_user_prompt(code, language, quest)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            response = self.client.chat_completion(
                messages=messages,
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            content = self.client.extract_content(response)
            analysis = json.loads(content)

            self._validate_analysis(analysis)

            cache.set(cache_key, analysis, self.cache_ttl)

            logger.info(f"Generated style analysis for quest {quest.id}: score {analysis['readability_score']}/10")
            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse style analysis JSON: {e}")
            raise ExecutionServiceUnavailable(f"Invalid JSON from LM Studio: {e}")
        except ExecutionServiceUnavailable as e:
            logger.error(f"LM Studio unavailable for style analysis: {e}")
            return self._get_fallback_analysis(code, language)
        except Exception as e:
            logger.error(f"Style analysis failed: {e}")
            raise

    def _build_system_prompt(self, language: str) -> str:
        """Build system prompt for LM Studio."""
        language_context = {
            'python': 'Python (PEP 8, list comprehensions, context managers, type hints)',
            'javascript': 'JavaScript (ES6+, arrow functions, async/await, destructuring)',
            'cpp': 'C++ (modern C++17+, RAII, const correctness, STL idioms)',
            'java': 'Java (naming conventions, design patterns, stream API, null safety)',
            'go': 'Go (simplicity, error handling, goroutines, interfaces)',
        }

        context = language_context.get(language, language)

        return (
            "You are a senior software engineer reviewing code for style, readability, and idiomatic patterns. "
            "This code is CORRECT — focus only on quality, not correctness. "
            "Provide constructive, actionable feedback that helps developers write better code. "
            "Respond ONLY in valid JSON with no markdown or extra text."
        )

    def _build_user_prompt(self, code: str, language: str, quest: Quest) -> str:
        """Build user prompt with code and requirements."""
        prompt = f"""Analyze this {language} code for style, readability, and idiomatic patterns.

Quest: {quest.title}
Language: {language}

Code:
```{language}
{code}
```

Evaluate and respond with ONLY this JSON structure (no markdown, no extra text):
{{
    "readability_score": <0-10 integer>,
    "naming_quality": "<brief assessment of variable/function naming>",
    "idiomatic_patterns": "<assessment of language idioms used>",
    "style_issues": [
        {{
            "issue": "<what could be improved>",
            "line_hint": "<approximate line or code snippet>",
            "suggestion": "<what to do instead>",
            "example_fix": "<code example of the fix>"
        }}
    ],
    "positive_patterns": [
        "<thing done well>",
        "<another strength>"
    ]
}}

Focus on:
1. Naming: Are variables/functions descriptive and idiomatic?
2. Readability: Is the code easy to understand?
3. Idioms: Are language-specific best practices used?
4. Style: Does it follow language conventions?

Be specific and actionable. Include 2-4 style issues if found, and 2-3 positive patterns."""

        return prompt

    def _validate_analysis(self, analysis: Dict[str, Any]) -> None:
        """Validate analysis has all required fields."""
        required_fields = ['readability_score', 'naming_quality', 'idiomatic_patterns', 'style_issues', 'positive_patterns']

        for field in required_fields:
            if field not in analysis:
                raise ValueError(f"Missing analysis field: {field}")

        if not isinstance(analysis['readability_score'], int) or not 0 <= analysis['readability_score'] <= 10:
            raise ValueError("readability_score must be integer 0-10")

        if not isinstance(analysis['style_issues'], list):
            raise ValueError("style_issues must be a list")

        if not isinstance(analysis['positive_patterns'], list):
            raise ValueError("positive_patterns must be a list")

        for issue in analysis['style_issues']:
            if not isinstance(issue, dict):
                raise ValueError("Each style issue must be a dictionary")
            required_issue_fields = ['issue', 'line_hint', 'suggestion', 'example_fix']
            for field in required_issue_fields:
                if field not in issue:
                    raise ValueError(f"Style issue missing field: {field}")

    def _get_cache_key(self, code: str, language: str, quest_id: int) -> str:
        """Generate cache key for style analysis."""
        import hashlib
        code_hash = hashlib.md5(code.encode()).hexdigest()[:8]
        return f"style_analysis:{quest_id}:{language}:{code_hash}"

    def _get_fallback_analysis(self, code: str, language: str) -> Dict[str, Any]:
        """Return fallback analysis when LM Studio unavailable."""
        lines = code.split('\n')
        line_count = len(lines)

        readability_score = 7
        if line_count > 100:
            readability_score = 6
        if line_count > 200:
            readability_score = 5

        return {
            'readability_score': readability_score,
            'naming_quality': 'Unable to analyze naming patterns at this time.',
            'idiomatic_patterns': 'Unable to analyze idiomatic patterns at this time.',
            'style_issues': [
                {
                    'issue': 'Unable to perform detailed style analysis',
                    'line_hint': 'Throughout code',
                    'suggestion': 'Try again when LM Studio is available for detailed feedback',
                    'example_fix': 'No specific fix available'
                }
            ],
            'positive_patterns': [
                'Code is syntactically correct',
                'Code structure is logical'
            ]
        }

    def is_available(self) -> bool:
        """Check if LM Studio is available for style analysis."""
        return self.client.is_available()


style_coach = CodeStyleCoach()
