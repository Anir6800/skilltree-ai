"""
AI Detection Service
Three-layer AI code authorship detection pipeline for SkillTree AI.
Layers: Embedding Similarity (35%), LLM Classification (45%), Heuristic Scoring (20%)
"""

import json
import logging
import re
import ast
import asyncio
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from django.conf import settings
from django.utils import timezone

from core.chroma_client import chroma_client
from core.lm_client import lm_client, ExecutionServiceUnavailable
from quests.models import QuestSubmission
from ai_detection.models import DetectionLog

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Result of AI detection analysis."""
    final_score: float
    embedding_score: float
    llm_score: float
    heuristic_score: float
    is_flagged: bool
    reasoning: str
    key_signals: List[str]
    llm_reasoning: Dict[str, Any]


class AIDetector:
    """
    Three-layer AI code detection pipeline.
    Combines embedding similarity, LLM classification, and heuristic analysis.
    """
    
    EMBEDDING_WEIGHT = 0.35
    LLM_WEIGHT = 0.45
    HEURISTIC_WEIGHT = 0.20
    FLAGGING_THRESHOLD = 0.70
    
    def __init__(self):
        self.chroma = chroma_client
        self.lm = lm_client
    
    async def detect(self, submission: QuestSubmission) -> DetectionResult:
        """
        Run complete AI detection pipeline on a submission.
        
        Args:
            submission: QuestSubmission instance to analyze
            
        Returns:
            DetectionResult with scores and reasoning
        """
        code = submission.code.strip()
        language = submission.language
        
        if not code:
            return DetectionResult(
                final_score=0.0,
                embedding_score=0.0,
                llm_score=0.0,
                heuristic_score=0.0,
                is_flagged=False,
                reasoning="Empty submission",
                key_signals=[],
                llm_reasoning={}
            )
        
        try:
            # Run layers 1 and 3 in parallel, layer 2 sequentially
            embedding_score, heuristic_score = await asyncio.gather(
                self._layer_1_embedding_similarity(code),
                self._layer_3_heuristic_scoring(code, language),
                return_exceptions=True
            )
            
            # Handle exceptions from parallel tasks
            if isinstance(embedding_score, Exception):
                logger.warning(f"Embedding layer failed: {embedding_score}")
                embedding_score = 0.5
            if isinstance(heuristic_score, Exception):
                logger.warning(f"Heuristic layer failed: {heuristic_score}")
                heuristic_score = 0.5
            
            # Layer 2 (LLM) runs after parallel tasks
            llm_score, llm_reasoning = await self._layer_2_llm_classification(code, language)
            
            # Compute final score
            final_score = (
                embedding_score * self.EMBEDDING_WEIGHT +
                llm_score * self.LLM_WEIGHT +
                heuristic_score * self.HEURISTIC_WEIGHT
            )
            
            # Determine if flagged
            is_flagged = final_score > self.FLAGGING_THRESHOLD
            
            # Build reasoning
            key_signals = self._extract_key_signals(
                embedding_score, llm_score, heuristic_score, llm_reasoning
            )
            reasoning = self._build_reasoning(
                final_score, embedding_score, llm_score, heuristic_score, key_signals
            )
            
            # Save detection log
            self._save_detection_log(
                submission, embedding_score, llm_score, heuristic_score,
                final_score, llm_reasoning
            )
            
            # Update submission
            submission.ai_detection_score = final_score
            if is_flagged:
                submission.status = 'flagged'
            submission.save(update_fields=['ai_detection_score', 'status'])
            
            return DetectionResult(
                final_score=round(final_score, 3),
                embedding_score=round(embedding_score, 3),
                llm_score=round(llm_score, 3),
                heuristic_score=round(heuristic_score, 3),
                is_flagged=is_flagged,
                reasoning=reasoning,
                key_signals=key_signals,
                llm_reasoning=llm_reasoning
            )
            
        except Exception as e:
            logger.error(f"AI detection failed for submission {submission.id}: {e}", exc_info=True)
            raise
    
    async def _layer_1_embedding_similarity(self, code: str) -> float:
        """
        Layer 1: Embedding Similarity (35% weight)
        Query ChromaDB for similar AI code samples.
        
        Args:
            code: Code to analyze
            
        Returns:
            Score 0-1 (higher = more AI-like)
        """
        try:
            # Query AI samples collection
            results = self.chroma.query_ai_samples(code, n_results=5)
            
            if not results or not results.get('distances'):
                return 0.0
            
            # Get max distance (closest match = highest similarity)
            distances = results['distances'][0] if results['distances'] else []
            if not distances:
                return 0.0
            
            # Normalize: ChromaDB returns distances 0-2, convert to 0-1
            # Lower distance = higher similarity = higher AI likelihood
            max_distance = max(distances)
            score = 1.0 - (max_distance / 2.0)
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.warning(f"Embedding similarity layer failed: {e}")
            return 0.5
    
    async def _layer_2_llm_classification(
        self, code: str, language: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Layer 2: LLM Classification (45% weight)
        Use LM Studio to classify code as AI-generated.
        
        Args:
            code: Code to analyze
            language: Programming language
            
        Returns:
            Tuple of (score 0-1, reasoning dict)
        """
        try:
            # Truncate code if too long (keep first 2000 chars)
            code_sample = code[:2000] if len(code) > 2000 else code
            
            system_prompt = (
                "You are an AI code authorship classifier. Analyze code for signs of AI generation. "
                "Respond ONLY with valid JSON."
            )
            
            user_prompt = (
                f"Analyze this {language} code for AI generation signs:\n\n"
                f"```{language}\n{code_sample}\n```\n\n"
                f"Signs of AI generation include:\n"
                f"- Excessive comments explaining obvious steps\n"
                f"- Generic variable names (result, temp, data, value)\n"
                f"- Overly clean/perfect structure\n"
                f"- Textbook-style solutions\n"
                f"- Repetitive patterns\n"
                f"- Unusual formatting or spacing\n\n"
                f"Respond with JSON: {{'is_ai_generated': bool, 'confidence': 0.0-1.0, "
                f"'reasoning': 'brief explanation', 'key_signals': ['signal1', 'signal2']}}"
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.lm.chat_completion(
                messages=messages,
                max_tokens=500,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = self.lm.extract_content(response)
            
            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    logger.warning(f"Could not parse LLM response: {content}")
                    return 0.5, {"error": "Invalid JSON response"}
            
            # Extract confidence
            is_ai = result.get('is_ai_generated', False)
            confidence = float(result.get('confidence', 0.5))
            confidence = max(0.0, min(1.0, confidence))
            
            # Score: if AI-generated, use confidence; otherwise use 1-confidence
            score = confidence if is_ai else (1.0 - confidence)
            
            reasoning = {
                "is_ai_generated": is_ai,
                "confidence": confidence,
                "reasoning": result.get('reasoning', ''),
                "key_signals": result.get('key_signals', [])
            }
            
            return score, reasoning
            
        except ExecutionServiceUnavailable as e:
            logger.warning(f"LM Studio unavailable: {e}")
            return 0.5, {"error": "LM Studio unavailable", "fallback": True}
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return 0.5, {"error": str(e)}
    
    async def _layer_3_heuristic_scoring(self, code: str, language: str) -> float:
        """
        Layer 3: Heuristic Scoring (20% weight)
        Analyze code patterns for AI generation indicators.
        
        Args:
            code: Code to analyze
            language: Programming language
            
        Returns:
            Score 0-1 (higher = more AI-like)
        """
        try:
            scores = []
            
            # Heuristic 1: Comment density
            comment_score = self._analyze_comment_density(code, language)
            scores.append(comment_score)
            
            # Heuristic 2: Identifier length
            identifier_score = self._analyze_identifier_length(code, language)
            scores.append(identifier_score)
            
            # Heuristic 3: Code repetition
            repetition_score = self._analyze_code_repetition(code)
            scores.append(repetition_score)
            
            # Heuristic 4: Generic naming patterns
            generic_score = self._analyze_generic_names(code, language)
            scores.append(generic_score)
            
            # Average all heuristic scores
            final_score = sum(scores) / len(scores) if scores else 0.5
            
            return max(0.0, min(1.0, final_score))
            
        except Exception as e:
            logger.warning(f"Heuristic scoring failed: {e}")
            return 0.5
    
    def _analyze_comment_density(self, code: str, language: str) -> float:
        """
        Analyze comment density. AI-generated code tends to over-comment.
        
        Returns:
            Score 0-1 (higher = more suspicious)
        """
        lines = code.split('\n')
        total_lines = len(lines)
        
        if total_lines == 0:
            return 0.0
        
        # Count comment lines
        comment_count = 0
        if language in ['python', 'py']:
            comment_count = sum(1 for line in lines if line.strip().startswith('#'))
        elif language in ['javascript', 'js', 'java', 'cpp', 'c++', 'go']:
            comment_count = sum(1 for line in lines if line.strip().startswith('//'))
        
        comment_density = comment_count / total_lines
        
        # Suspicious if > 30% comments
        if comment_density > 0.3:
            return min(1.0, (comment_density - 0.3) / 0.2)
        
        return 0.0
    
    def _analyze_identifier_length(self, code: str, language: str) -> float:
        """
        Analyze average identifier length. AI tends toward longer descriptive names.
        
        Returns:
            Score 0-1 (higher = more suspicious)
        """
        try:
            identifiers = []
            
            if language in ['python', 'py']:
                try:
                    tree = ast.parse(code)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Name):
                            identifiers.append(node.id)
                        elif isinstance(node, ast.FunctionDef):
                            identifiers.append(node.name)
                        elif isinstance(node, ast.ClassDef):
                            identifiers.append(node.name)
                except SyntaxError:
                    pass
            
            # Fallback: regex-based identifier extraction
            if not identifiers:
                pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
                identifiers = re.findall(pattern, code)
            
            if not identifiers:
                return 0.0
            
            avg_length = sum(len(i) for i in identifiers) / len(identifiers)
            
            # Suspicious if average > 15 characters
            if avg_length > 15:
                return min(1.0, (avg_length - 15) / 10)
            
            return 0.0
            
        except Exception as e:
            logger.debug(f"Identifier length analysis failed: {e}")
            return 0.0
    
    def _analyze_code_repetition(self, code: str) -> float:
        """
        Analyze code repetition patterns. AI tends to repeat patterns.
        
        Returns:
            Score 0-1 (higher = more suspicious)
        """
        try:
            lines = [line.strip() for line in code.split('\n') if line.strip()]
            
            if len(lines) < 2:
                return 0.0
            
            # Count repeated lines
            line_counts = {}
            for line in lines:
                line_counts[line] = line_counts.get(line, 0) + 1
            
            # Calculate repetition ratio
            repeated_lines = sum(1 for count in line_counts.values() if count > 1)
            repetition_ratio = repeated_lines / len(line_counts) if line_counts else 0.0
            
            # Suspicious if > 20% repetition
            if repetition_ratio > 0.2:
                return min(1.0, (repetition_ratio - 0.2) / 0.3)
            
            return 0.0
            
        except Exception as e:
            logger.debug(f"Repetition analysis failed: {e}")
            return 0.0
    
    def _analyze_generic_names(self, code: str, language: str) -> float:
        """
        Analyze use of generic variable names. AI uses generic names less often.
        
        Returns:
            Score 0-1 (higher = more suspicious)
        """
        generic_names = {'result', 'temp', 'data', 'value', 'item', 'obj', 'x', 'y', 'z', 'i', 'j', 'k'}
        
        try:
            identifiers = []
            
            if language in ['python', 'py']:
                try:
                    tree = ast.parse(code)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Name):
                            identifiers.append(node.id.lower())
                except SyntaxError:
                    pass
            
            if not identifiers:
                pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
                identifiers = [i.lower() for i in re.findall(pattern, code)]
            
            if not identifiers:
                return 0.0
            
            generic_count = sum(1 for i in identifiers if i in generic_names)
            generic_ratio = generic_count / len(identifiers)
            
            # Suspicious if < 5% generic names (AI uses more descriptive names)
            if generic_ratio < 0.05:
                return min(1.0, (0.05 - generic_ratio) / 0.05)
            
            return 0.0
            
        except Exception as e:
            logger.debug(f"Generic names analysis failed: {e}")
            return 0.0
    
    def _extract_key_signals(
        self,
        embedding_score: float,
        llm_score: float,
        heuristic_score: float,
        llm_reasoning: Dict[str, Any]
    ) -> List[str]:
        """Extract key signals from all layers."""
        signals = []
        
        if embedding_score > 0.6:
            signals.append("Similar to known AI samples")
        
        if llm_reasoning.get('key_signals'):
            signals.extend(llm_reasoning['key_signals'][:2])
        
        if heuristic_score > 0.6:
            signals.append("Suspicious code patterns detected")
        
        return signals[:3]
    
    def _build_reasoning(
        self,
        final_score: float,
        embedding_score: float,
        llm_score: float,
        heuristic_score: float,
        key_signals: List[str]
    ) -> str:
        """Build human-readable reasoning."""
        if final_score > self.FLAGGING_THRESHOLD:
            return (
                f"Code flagged as likely AI-generated (score: {final_score:.1%}). "
                f"Signals: {', '.join(key_signals) if key_signals else 'Multiple indicators'}"
            )
        elif final_score > 0.5:
            return (
                f"Code shows some AI-like characteristics (score: {final_score:.1%}). "
                f"Review recommended."
            )
        else:
            return f"Code appears human-written (score: {final_score:.1%})"
    
    def _save_detection_log(
        self,
        submission: QuestSubmission,
        embedding_score: float,
        llm_score: float,
        heuristic_score: float,
        final_score: float,
        llm_reasoning: Dict[str, Any]
    ) -> None:
        """Save detection results to database."""
        try:
            DetectionLog.objects.create(
                submission=submission,
                embedding_score=embedding_score,
                llm_score=llm_score,
                heuristic_score=heuristic_score,
                final_score=final_score,
                llm_reasoning=llm_reasoning
            )
        except Exception as e:
            logger.error(f"Failed to save detection log: {e}")


# Singleton instance
ai_detector = AIDetector()
