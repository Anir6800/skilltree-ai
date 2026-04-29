"""
AI Evaluation Service with RAG Pipeline
Evaluates code submissions using ChromaDB context and LM Studio.
"""

import json
import logging
import hashlib
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.conf import settings

from core.chroma_client import chroma_client
from core.lm_client import lm_client, ExecutionServiceUnavailable

logger = logging.getLogger(__name__)


class AIEvaluator:
    """
    RAG-based code evaluation using ChromaDB and LM Studio.
    Provides detailed feedback with skill-specific context.
    """
    
    def __init__(self):
        self.chroma = chroma_client
        self.lm = lm_client
        self.cache_ttl = 86400  # 24 hours
        self.max_retries = 2
    
    def _generate_cache_key(self, code: str, quest_id: int, language: str = 'python') -> str:
        """Generate cache key from code, quest ID, and language."""
        content = f"{quest_id}:{language}:{code}"
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        return f"ai_eval:{hash_obj.hexdigest()}"
    
    def _get_cached_feedback(self, code: str, quest_id: int, language: str = 'python') -> Optional[Dict[str, Any]]:
        """Retrieve cached feedback if available."""
        cache_key = self._generate_cache_key(code, quest_id, language)
        return cache.get(cache_key)
    
    def _cache_feedback(self, code: str, quest_id: int, language: str = 'python', feedback: Dict[str, Any] = None):
        """Cache feedback for future requests."""
        cache_key = self._generate_cache_key(code, quest_id, language)
        cache.set(cache_key, feedback, self.cache_ttl)
    
    def _retrieve_rag_context(self, code: str, language: str, quest_description: str) -> str:
        """
        Retrieve relevant context from ChromaDB.
        
        Args:
            code: Submitted code
            language: Programming language
            quest_description: Quest description
            
        Returns:
            Formatted context string
        """
        # Query skill knowledge with code + description
        query_text = f"{quest_description}\n\nCode ({language}):\n{code}"
        skill_results = self.chroma.query_skill_knowledge(query_text, n_results=3)
        
        if not skill_results:
            return "No specific skill context available."
        
        # Format context
        context_parts = ["=== RELEVANT SKILL KNOWLEDGE ===\n"]
        for i, result in enumerate(skill_results, 1):
            doc = result['document']
            metadata = result['metadata']
            context_parts.append(
                f"Context {i} (Skill: {metadata.get('title', 'Unknown')}, "
                f"Category: {metadata.get('category', 'N/A')}):\n{doc}\n"
            )
        
        return "\n".join(context_parts)
    
    def _build_evaluation_prompt(
        self,
        code: str,
        language: str,
        quest_title: str,
        quest_description: str,
        test_cases: list,
        rag_context: str,
        execution_result: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build structured evaluation prompt.
        
        Args:
            code: Submitted code
            language: Programming language
            quest_title: Quest title
            quest_description: Quest description
            test_cases: List of test cases
            rag_context: RAG-retrieved context
            execution_result: Optional execution result from sandbox
            
        Returns:
            Formatted prompt string
        """
        # Format test cases
        test_cases_str = "\n".join([
            f"  Test {i+1}: Input='{tc.get('input', '')}' \u2192 Expected='{tc.get('expected_output', tc.get('expected', ''))}'"
            for i, tc in enumerate(test_cases[:5])  # Limit to 5 for prompt size
        ])
        
        # Format execution context
        test_summary = "No execution data available."
        has_output = "No"
        if execution_result:
            results = execution_result.get('test_results', [])
            passed = sum(1 for r in results if r.get('status') == 'passed')
            total = len(results)
            test_summary = f"{passed}/{total} test cases passed."
            if execution_result.get('output') or execution_result.get('stdout'):
                has_output = "Yes"
        
        prompt = f"""You are an expert code reviewer for SkillTree AI, a developer learning platform. Evaluate the submitted code against the quest requirements and best practices.

QUEST: {quest_title}
DESCRIPTION: {quest_description}

TEST CASES:
{test_cases_str}

SUBMITTED CODE ({language}):
```{language}
{code}
```

{rag_context}

Evaluate the code for:
1. Correctness - Does it solve the problem? (Crucial: Check if it produces the expected output for the given inputs)
2. Code Quality - Is it clean, readable, maintainable?
3. Efficiency - Time and space complexity
4. Best Practices - Follows language conventions?
5. Learning Value - Does it demonstrate understanding?

CONTEXT ON EXECUTION:
The code was executed against test cases in a sandbox.
Summary: {test_summary}
Output detected in stdout: {has_output}

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "score": 85,
  "summary": "Brief 1-2 sentence overall assessment",
  "pros": ["Strength 1", "Strength 2", "Strength 3"],
  "cons": ["Weakness 1", "Weakness 2"],
  "improvements": [
    {{
      "issue": "Specific issue found",
      "suggestion": "How to improve it",
      "example": "Code example if applicable"
    }}
  ],
  "time_complexity": "O(n)",
  "space_complexity": "O(1)"
}}

Ensure:
- score is 0-100 integer
- pros array has 2-4 items
- cons array has 1-3 items (or empty if perfect)
- If the code logic is correct but output is empty, explicitly mention that they might have forgotten to print the result or read from stdin.
- improvements array has 1-3 items with issue/suggestion/example
- complexities use Big-O notation
- Response is valid JSON only, no markdown formatting"""
        
        return prompt
    
    def _parse_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LM Studio response and extract structured feedback.
        
        Args:
            response_text: Raw response from LM Studio
            
        Returns:
            Parsed feedback dictionary
            
        Raises:
            ValueError: If response is not valid JSON
        """
        # Remove markdown code blocks if present
        text = response_text.strip()
        
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
            if text.startswith("json"):
                text = text[4:].strip()
        
        try:
            feedback = json.loads(text)
            
            # Validate required fields
            required_fields = ['score', 'summary', 'pros', 'cons', 'improvements']
            for field in required_fields:
                if field not in feedback:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure score is in range
            feedback['score'] = max(0, min(100, int(feedback['score'])))
            
            # Ensure arrays
            if not isinstance(feedback['pros'], list):
                feedback['pros'] = []
            if not isinstance(feedback['cons'], list):
                feedback['cons'] = []
            if not isinstance(feedback['improvements'], list):
                feedback['improvements'] = []
            
            return feedback
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {text[:200]}")
    
    def _evaluate_with_retry(
        self,
        code: str,
        language: str,
        quest_title: str,
        quest_description: str,
        test_cases: list,
        rag_context: str,
        execution_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate code with retry logic for malformed responses.
        
        Args:
            code: Submitted code
            language: Programming language
            quest_title: Quest title
            quest_description: Quest description
            test_cases: Test cases
            rag_context: RAG context
            
        Returns:
            Parsed feedback dictionary
        """
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"[EVAL] Attempt {attempt + 1}/{self.max_retries + 1} to evaluate code")
                
                # Build prompt (simplified on retry)
                if attempt == 0:
                    prompt = self._build_evaluation_prompt(
                        code, language, quest_title, quest_description,
                        test_cases, rag_context, execution_result
                    )
                else:
                    # Simplified prompt for retry
                    prompt = f"""Evaluate this {language} code and respond with ONLY valid JSON:

Code:
```{language}
{code}
```

Required JSON format:
{{"score":85,"summary":"...","pros":["..."],"cons":["..."],"improvements":[{{"issue":"...","suggestion":"...","example":"..."}}],"time_complexity":"O(n)","space_complexity":"O(1)"}}"""
                
                logger.info(f"[EVAL] Sending request to LM Studio (attempt {attempt + 1})")
                logger.debug(f"[EVAL] Prompt length: {len(prompt)} chars")
                
                # Call LM Studio with timeout
                messages = [
                    {
                        "role": "system",
                        "content": "You are a code reviewer. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
                
                response = self.lm.chat_completion(
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.2
                )
                
                logger.info(f"[EVAL] LM Studio response received successfully")
                
                # Extract and parse
                response_text = self.lm.extract_content(response)
                logger.debug(f"[EVAL] Response text: {response_text[:200]}...")
                
                parsed = self._parse_evaluation_response(response_text)
                logger.info(f"[EVAL] Response parsed successfully: score={parsed.get('score')}")
                return parsed
                
            except (ValueError, ExecutionServiceUnavailable, TimeoutError) as e:
                logger.warning(f"[EVAL] Attempt {attempt + 1} failed: {type(e).__name__}: {str(e)}")
                
                if attempt >= self.max_retries:
                    # Return fallback feedback
                    logger.error(f"[EVAL] All {self.max_retries + 1} attempts failed, returning fallback")
                    return {
                        "score": 50,
                        "summary": f"Evaluation service unavailable or timeout",
                        "pros": ["Code submitted successfully"],
                        "cons": ["Unable to complete AI evaluation"],
                        "improvements": [],
                        "time_complexity": "Unknown",
                        "space_complexity": "Unknown",
                        "error": str(e)[:100]
                    }
                # Retry with simplified prompt
                logger.info(f"[EVAL] Retrying with simplified prompt...")
                continue
        
        # Should not reach here
        logger.error(f"[EVAL] Unexpected: reached end of retry loop")
        return {
            "score": 50,
            "summary": "Evaluation incomplete",
            "pros": [],
            "cons": [],
            "improvements": [],
            "time_complexity": "Unknown",
            "space_complexity": "Unknown"
        }
    
    def evaluate(self, submission) -> Dict[str, Any]:
        """
        Main evaluation pipeline with RAG and caching.
        
        Args:
            submission: QuestSubmission instance
            
        Returns:
            Feedback dictionary with score, summary, pros, cons, improvements
        """
        logger.info(f"[EVAL] Starting evaluation for submission {submission.id}")
        
        # Check cache first - INCLUDE LANGUAGE
        cached = self._get_cached_feedback(submission.code, submission.quest.id, submission.language)
        if cached:
            logger.info(f"[EVAL] Cache hit for submission {submission.id}")
            return cached
        
        logger.info(f"[EVAL] Cache miss, proceeding with LM Studio evaluation")
        
        # Step 1: Retrieve RAG context
        logger.info(f"[EVAL] Retrieving RAG context for submission {submission.id}")
        rag_context = self._retrieve_rag_context(
            submission.code,
            submission.language,
            submission.quest.description
        )
        logger.info(f"[EVAL] RAG context retrieved: {len(rag_context)} chars")
        
        # Step 2: Evaluate with LM Studio
        logger.info(f"[EVAL] Calling LM Studio for submission {submission.id}")
        feedback = self._evaluate_with_retry(
            code=submission.code,
            language=submission.language,
            quest_title=submission.quest.title,
            quest_description=submission.quest.description,
            test_cases=submission.quest.test_cases,
            rag_context=rag_context,
            execution_result=submission.execution_result
        )
        logger.info(f"[EVAL] LM Studio response received: score={feedback.get('score')}")
        
        # Step 3: Cache result - INCLUDE LANGUAGE
        self._cache_feedback(submission.code, submission.quest.id, submission.language, feedback)
        
        # Step 4: Store in submission
        submission.ai_feedback = feedback
        submission.save(update_fields=['ai_feedback'])
        
        logger.info(f"[EVAL] Evaluation complete for submission {submission.id}")
        return feedback
    
    def is_available(self) -> bool:
        """Check if evaluation service is available."""
        return self.lm.is_available()


# Singleton instance
ai_evaluator = AIEvaluator()
