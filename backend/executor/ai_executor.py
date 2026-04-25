"""
AI-Powered Code Execution Simulator
Uses LM Studio to predict code execution results without running actual code.
Useful for quick feedback, learning scenarios, and when Docker is unavailable.
"""

import json
from typing import List, Dict, Any

from core.lm_client import lm_client, ExecutionServiceUnavailable


class AIExecutor:
    """
    AI-based code execution simulator using LM Studio.
    Predicts execution results through structured prompting.
    """
    
    def __init__(self):
        self.client = lm_client
    
    def _build_simulation_prompt(
        self,
        code: str,
        language: str,
        test_cases: List[Dict[str, str]]
    ) -> str:
        """
        Build structured prompt for AI simulation.
        
        Args:
            code: Source code to simulate
            language: Programming language
            test_cases: List of test cases with input/expected output
            
        Returns:
            Formatted prompt string
        """
        test_cases_str = "\n".join([
            f"Test {i+1}:\n  Input: {tc.get('input', '(no input)')}\n  Expected: {tc.get('expected', '')}"
            for i, tc in enumerate(test_cases)
        ])
        
        prompt = f"""You are a code execution simulator. Given the following {language} code and test cases, predict the exact output for each input.

CODE:
```{language}
{code}
```

TEST CASES:
{test_cases_str}

Analyze the code logic carefully and predict what output it would produce for each test case input.

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "results": [
    {{
      "input": "test input here",
      "predicted_output": "exact output the code would produce",
      "would_pass": true,
      "reasoning": "brief explanation of why this output is expected"
    }}
  ],
  "overall_assessment": "brief summary of code correctness and potential issues"
}}

Ensure:
- predicted_output matches exactly what the code would print (including whitespace/newlines)
- would_pass is true only if predicted_output matches the expected output
- Include all {len(test_cases)} test cases in results array
- Response is valid JSON only, no markdown formatting"""
        
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse AI response and extract structured data.
        
        Args:
            response_text: Raw text response from LM Studio
            
        Returns:
            Parsed dictionary with results
            
        Raises:
            ValueError: If response is not valid JSON
        """
        # Try to extract JSON from response (handle markdown code blocks)
        text = response_text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (``` markers)
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
            # Remove language identifier if present
            if text.startswith("json"):
                text = text[4:].strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {e}\nResponse: {text[:200]}")
    
    def simulate_execution(
        self,
        code: str,
        language: str,
        test_cases: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Simulate code execution using AI prediction.
        
        Args:
            code: Source code to simulate
            language: Programming language (python, javascript, cpp, java, go)
            test_cases: List of {"input": str, "expected": str} dictionaries
            
        Returns:
            Dictionary matching CompileExecutor.run_test_cases() format with is_simulated flag
        """
        # Validate inputs
        if not code or not code.strip():
            return {
                "tests_passed": 0,
                "tests_total": len(test_cases),
                "results": [],
                "is_simulated": True,
                "error": "Empty code provided"
            }
        
        if not test_cases:
            return {
                "tests_passed": 0,
                "tests_total": 0,
                "results": [],
                "is_simulated": True
            }
        
        try:
            # Build prompt
            prompt = self._build_simulation_prompt(code, language, test_cases)
            
            # Call LM Studio
            messages = [
                {
                    "role": "system",
                    "content": "You are a precise code execution simulator. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self.client.chat_completion(
                messages=messages,
                max_tokens=2000,
                temperature=0.1
            )
            
            # Extract and parse response
            response_text = self.client.extract_content(response)
            ai_data = self._parse_ai_response(response_text)
            
            # Transform AI response to match CompileExecutor format
            results = []
            tests_passed = 0
            
            for i, test_case in enumerate(test_cases):
                # Get corresponding AI prediction
                if i < len(ai_data.get("results", [])):
                    ai_result = ai_data["results"][i]
                    predicted = ai_result.get("predicted_output", "").strip()
                    expected = test_case.get("expected", "").strip()
                    passed = predicted == expected
                    
                    if passed:
                        tests_passed += 1
                    
                    results.append({
                        "input": test_case.get("input", ""),
                        "expected": expected,
                        "actual": predicted,
                        "passed": passed,
                        "time_ms": 0,  # AI simulation has no execution time
                        "status": "ok",
                        "reasoning": ai_result.get("reasoning", "")
                    })
                else:
                    # Fallback if AI didn't provide enough results
                    results.append({
                        "input": test_case.get("input", ""),
                        "expected": test_case.get("expected", ""),
                        "actual": "",
                        "passed": False,
                        "time_ms": 0,
                        "status": "error",
                        "reasoning": "AI did not provide prediction for this test case"
                    })
            
            return {
                "tests_passed": tests_passed,
                "tests_total": len(test_cases),
                "results": results,
                "is_simulated": True,
                "overall_assessment": ai_data.get("overall_assessment", "")
            }
            
        except ExecutionServiceUnavailable as e:
            return {
                "tests_passed": 0,
                "tests_total": len(test_cases),
                "results": [],
                "is_simulated": True,
                "error": f"AI service unavailable: {str(e)}"
            }
        except ValueError as e:
            return {
                "tests_passed": 0,
                "tests_total": len(test_cases),
                "results": [],
                "is_simulated": True,
                "error": f"Failed to parse AI response: {str(e)}"
            }
        except Exception as e:
            return {
                "tests_passed": 0,
                "tests_total": len(test_cases),
                "results": [],
                "is_simulated": True,
                "error": f"Simulation error: {str(e)}"
            }
    
    def is_available(self) -> bool:
        """
        Check if AI execution service is available.
        
        Returns:
            True if LM Studio is reachable, False otherwise
        """
        return self.client.is_available()


# Singleton instance
ai_executor = AIExecutor()
