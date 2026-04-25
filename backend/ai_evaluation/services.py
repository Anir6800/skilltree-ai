"""
AI Evaluation Service with RAG Pipeline
Evaluates code submissions using ChromaDB context and LM Studio.
"""

import json
import hashlib
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.conf import settings

from core.chroma_client import chroma_client
from core.lm_client import lm_client, ExecutionServiceUnavailable


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
    
    def _generate_cache_key(self, code: str, quest_id: int) -> str:
        """Generate cache key from code and quest ID."""
        content = f"{quest_id}:{code}"
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        return f"ai_eval:{hash_obj.hexdigest()}"
    
    def _get_cached_feedback(self, code: str, quest_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached feedback if available."""
        cache_key = self._generate_cache_key(code, quest_id)
        return cache.get(cache_key)
    
    def _cache_feedback(self, code: str, quest_id: int, feedback: Dict[str, Any]):
        """Cache feedback for future requests."""
        cache_key = self._generate_cache_key(code, quest_id)
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
        rag_context: str
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
            
        Returns:
            Formatted prompt string
        """
        # Format test cases
        test_cases_str = "\n".join([
            f"  Test {i+1}: Input='{tc.get('input', '')}' → Expected='{tc.get('expected_output', tc.get('expected', ''))}'"
            for i, tc in enumerate(test_cases[:5])  # Limit to 5 for prompt size
        ])
        
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
1. Correctness - Does it solve the problem?
2. Code Quality - Is it clean, readable, maintainable?
3. Efficiency - Time and space complexity
4. Best Practices - Follows language conventions?
5. Learning Value - Does it demonstrate understanding?

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
        rag_context: str
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
                # Build prompt (simplified on retry)
                if attempt == 0:
                    prompt = self._build_evaluation_prompt(
                        code, language, quest_title, quest_description,
                        test_cases, rag_context
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
                
                # Call LM Studio
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
                
                # Extract and parse
                response_text = self.lm.extract_content(response)
                return self._parse_evaluation_response(response_text)
                
            except (ValueError, ExecutionServiceUnavailable) as e:
                if attempt >= self.max_retries:
                    # Return fallback feedback
                    return {
                        "score": 50,
                        "summary": f"Evaluation failed: {str(e)[:100]}",
                        "pros": ["Code submitted successfully"],
                        "cons": ["Unable to complete AI evaluation"],
                        "improvements": [],
                        "time_complexity": "Unknown",
                        "space_complexity": "Unknown",
                        "error": str(e)
                    }
                # Retry with simplified prompt
                continue
        
        # Should not reach here
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
        # Check cache first
        cached = self._get_cached_feedback(submission.code, submission.quest.id)
        if cached:
            return cached
        
        # Step 1: Retrieve RAG context
        rag_context = self._retrieve_rag_context(
            submission.code,
            submission.language,
            submission.quest.description
        )
        
        # Step 2: Evaluate with LM Studio
        feedback = self._evaluate_with_retry(
            code=submission.code,
            language=submission.language,
            quest_title=submission.quest.title,
            quest_description=submission.quest.description,
            test_cases=submission.quest.test_cases,
            rag_context=rag_context
        )
        
        # Step 3: Cache result
        self._cache_feedback(submission.code, submission.quest.id, feedback)
        
        # Step 4: Store in submission
        submission.ai_feedback = feedback
        submission.save(update_fields=['ai_feedback'])
        
        return feedback
    
    def is_available(self) -> bool:
        """Check if evaluation service is available."""
        return self.lm.is_available()


# Singleton instance
ai_evaluator = AIEvaluator()
