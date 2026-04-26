"""
Assessment Engine
Multi-type evaluation system for MCQ, code challenges, and open-ended questions.
Integrates with CompileExecutor for code sandbox and LM Studio for semantic evaluation.
"""

import json
from typing import Dict, Any, List, Optional
from django.conf import settings
from executor.services import CompileExecutor
from core.lm_client import LMStudioClient, ExecutionServiceUnavailable


class EvaluationResult:
    """
    Structured result from assessment evaluation.
    """
    def __init__(
        self,
        passed: Optional[bool],
        score: float,
        feedback: str,
        test_results: Optional[List[Dict[str, Any]]] = None,
        criteria_met: Optional[bool] = None,
        missing_points: Optional[List[str]] = None,
        error: Optional[str] = None
    ):
        self.passed = passed
        self.score = score
        self.feedback = feedback
        self.test_results = test_results or []
        self.criteria_met = criteria_met
        self.missing_points = missing_points or []
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "passed": self.passed,
            "score": self.score,
            "feedback": self.feedback,
            "test_results": self.test_results,
            "criteria_met": self.criteria_met,
            "missing_points": self.missing_points,
            "error": self.error
        }


class AssessmentEngine:
    """
    Core assessment evaluation engine.
    Handles MCQ instant scoring, code execution sandbox, and LM Studio semantic evaluation.
    """
    
    def __init__(self):
        self.executor = CompileExecutor()
        self.lm_client = LMStudioClient()
    
    def evaluate(self, submission) -> EvaluationResult:
        """
        Evaluate an assessment submission based on question type.
        
        Args:
            submission: AssessmentSubmission instance with user, question, answer
            
        Returns:
            EvaluationResult with passed status, score, and feedback
        """
        question = submission.question
        question_type = question.question_type
        
        try:
            if question_type == "mcq":
                return self._evaluate_mcq(submission)
            elif question_type == "code":
                return self._evaluate_code(submission)
            elif question_type == "open_ended":
                return self._evaluate_open_ended(submission)
            else:
                return EvaluationResult(
                    passed=False,
                    score=0.0,
                    feedback=f"Unknown question type: {question_type}",
                    error="invalid_question_type"
                )
        except Exception as e:
            return EvaluationResult(
                passed=False,
                score=0.0,
                feedback=f"Evaluation error: {str(e)}",
                error="evaluation_exception"
            )
    
    def _evaluate_mcq(self, submission) -> EvaluationResult:
        """
        Evaluate multiple choice question.
        Instant comparison of submitted answer with correct answer.
        """
        question = submission.question
        user_answer = submission.answer.strip()
        correct_answer = question.correct_answer.strip()
        
        # Support both option index (e.g., "0", "1") and option text
        is_correct = user_answer == correct_answer
        
        # Try matching by option text if direct match fails
        if not is_correct and question.mcq_options:
            try:
                # Check if user submitted option text instead of index
                user_option_index = None
                correct_option_index = None
                
                for idx, option in enumerate(question.mcq_options):
                    if str(option).strip() == user_answer:
                        user_option_index = idx
                    if str(option).strip() == correct_answer or str(idx) == correct_answer:
                        correct_option_index = idx
                
                if user_option_index is not None and correct_option_index is not None:
                    is_correct = user_option_index == correct_option_index
            except (ValueError, IndexError):
                pass
        
        if is_correct:
            return EvaluationResult(
                passed=True,
                score=question.points,
                feedback="Correct! Well done."
            )
        else:
            # Build feedback with correct answer
            correct_text = correct_answer
            if question.mcq_options:
                try:
                    correct_idx = int(correct_answer)
                    if 0 <= correct_idx < len(question.mcq_options):
                        correct_text = question.mcq_options[correct_idx]
                except (ValueError, IndexError):
                    pass
            
            return EvaluationResult(
                passed=False,
                score=0.0,
                feedback=f"Incorrect. The correct answer was: {correct_text}"
            )
    
    def _evaluate_code(self, submission) -> EvaluationResult:
        """
        Evaluate code challenge using CompileExecutor sandbox.
        Runs test cases and calculates score based on pass rate.
        """
        question = submission.question
        user_code = submission.answer
        test_cases = question.test_cases
        
        if not test_cases:
            return EvaluationResult(
                passed=False,
                score=0.0,
                feedback="No test cases defined for this question.",
                error="no_test_cases"
            )
        
        # Detect language from question or default to python
        language = getattr(question, 'language', 'python')
        
        # Run test cases through executor
        try:
            test_result = self.executor.run_test_cases(
                code=user_code,
                language=language,
                test_cases=test_cases
            )
        except Exception as e:
            return EvaluationResult(
                passed=False,
                score=0.0,
                feedback=f"Execution error: {str(e)}",
                error="execution_failed"
            )
        
        tests_passed = test_result["tests_passed"]
        tests_total = test_result["tests_total"]
        test_results = test_result["results"]
        
        # Calculate score based on pass rate
        pass_rate = tests_passed / tests_total if tests_total > 0 else 0
        score = pass_rate * question.points
        
        # Determine if passed (70% threshold)
        passed = pass_rate >= 0.7
        
        # Build feedback
        if passed:
            feedback = f"Great work! Passed {tests_passed}/{tests_total} test cases."
        else:
            feedback = f"Passed {tests_passed}/{tests_total} test cases. Review the failed cases and try again."
        
        return EvaluationResult(
            passed=passed,
            score=round(score, 2),
            feedback=feedback,
            test_results=test_results
        )
    
    def _evaluate_open_ended(self, submission) -> EvaluationResult:
        """
        Evaluate open-ended question using LM Studio semantic analysis.
        Checks if answer satisfies validation criteria.
        """
        question = submission.question
        user_answer = submission.answer
        validation_criteria = question.validation_criteria
        
        # Check if LM Studio is available
        if not self.lm_client.is_available():
            return EvaluationResult(
                passed=None,
                score=0.0,
                feedback="Evaluation pending — AI service unavailable. Your answer has been saved and will be evaluated when the service is restored.",
                error="ai_service_unavailable"
            )
        
        # Build evaluation prompt
        system_prompt = (
            "You are an educational assessor. Evaluate if a student's answer satisfies the given criteria. "
            "Be fair and concise. Provide constructive feedback."
        )
        
        user_prompt = (
            f"Question: {question.prompt}\n\n"
            f"Criteria to satisfy: {validation_criteria}\n\n"
            f"Student answer: {user_answer}\n\n"
            f"Respond with JSON in this exact format:\n"
            f"{{\n"
            f'  "criteria_met": true or false,\n'
            f'  "score_percent": 0-100,\n'
            f'  "feedback": "constructive one-paragraph feedback",\n'
            f'  "missing_points": ["point 1", "point 2"]\n'
            f"}}"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # Request JSON response format
            response = self.lm_client.chat_completion(
                messages=messages,
                max_tokens=500,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = self.lm_client.extract_content(response)
            
            # Parse JSON response
            try:
                evaluation = json.loads(content)
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from markdown code blocks
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                    evaluation = json.loads(content)
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                    evaluation = json.loads(content)
                else:
                    raise
            
            # Extract evaluation fields
            criteria_met = evaluation.get("criteria_met", False)
            score_percent = evaluation.get("score_percent", 0)
            feedback = evaluation.get("feedback", "No feedback provided.")
            missing_points = evaluation.get("missing_points", [])
            
            # Calculate score
            score = (score_percent / 100.0) * question.points
            
            return EvaluationResult(
                passed=criteria_met,
                score=round(score, 2),
                feedback=feedback,
                criteria_met=criteria_met,
                missing_points=missing_points
            )
            
        except ExecutionServiceUnavailable as e:
            return EvaluationResult(
                passed=None,
                score=0.0,
                feedback=f"Evaluation pending — AI service error: {str(e)}",
                error="ai_service_error"
            )
        except json.JSONDecodeError as e:
            return EvaluationResult(
                passed=None,
                score=0.0,
                feedback="Evaluation pending — AI response format error. Your answer has been saved.",
                error="ai_response_parse_error"
            )
        except Exception as e:
            return EvaluationResult(
                passed=None,
                score=0.0,
                feedback=f"Evaluation pending — Unexpected error: {str(e)}",
                error="evaluation_exception"
            )


# Singleton instance
assessment_engine = AssessmentEngine()
