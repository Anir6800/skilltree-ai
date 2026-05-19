"""
SkillTree AI - Robust Quest Generator
======================================
Production-ready AI quest generation pipeline with:
- Strong system prompts optimized for GPT-OSS-20B
- JSON schema validation
- Output repair layer for malformed responses
- Retry mechanism with exponential backoff
- Fallback generation for when AI is unavailable
- Comprehensive quest enrichment pipeline

Quest Schema (REQUIRED FIELDS):
{
    "title": "Quest Title",
    "description": "Full problem statement with examples",
    "difficulty": 1-5,
    "xpReward": 100-500,
    "estimatedTime": "15 minutes",
    "objectives": ["Objective 1", "Objective 2"],
    "skillsGained": ["Skill 1", "Skill 2"],
    "prerequisites": ["Prerequisite 1"],
    "completionCriteria": ["Criterion 1", "Criterion 2"],
    "resources": ["Resource 1"],
    "starterCode": "Python code with TODO",
    "testCases": [
        {"input": "...", "expectedOutput": "...", "hint": "One-line hint"}
    ],
    "difficultyMultiplier": 1.0-3.0,
    "type": "coding" | "debugging" | "mcq"
}
"""

import json
import re
import logging
import time
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.core.cache import cache
from core.lm_client import lm_client, ExecutionServiceUnavailable

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Quest Schema Definition
# ─────────────────────────────────────────────────────────────────────────────

QUEST_SCHEMA = {
    "type": "object",
    "required": [
        "title", "description", "difficulty", "xpReward", "estimatedTime",
        "objectives", "skillsGained", "prerequisites", "completionCriteria",
        "resources", "starterCode", "testCases", "difficultyMultiplier", "type"
    ],
    "properties": {
        "title": {"type": "string", "minLength": 5, "maxLength": 100},
        "description": {"type": "string", "minLength": 50, "maxLength": 2000},
        "difficulty": {"type": "integer", "minimum": 1, "maximum": 5},
        "xpReward": {"type": "integer", "minimum": 100, "maximum": 500},
        "estimatedTime": {"type": "string", "pattern": r"^\d+\s*(minutes?|hours?)$"},
        "objectives": {"type": "array", "minItems": 1, "maxItems": 5},
        "skillsGained": {"type": "array", "minItems": 1, "maxItems": 5},
        "prerequisites": {"type": "array", "minItems": 0, "maxItems": 3},
        "completionCriteria": {"type": "array", "minItems": 1, "maxItems": 5},
        "resources": {"type": "array", "minItems": 0, "maxItems": 5},
        "starterCode": {"type": "string", "minLength": 10},
        "testCases": {
            "type": "array",
            "minItems": 3,
            "maxItems": 10,
            "items": {
                "type": "object",
                "required": ["input", "expectedOutput"],
                "properties": {
                    "input": {"type": "string"},
                    "expectedOutput": {"type": "string"},
                    "hint": {"type": "string"}
                }
            }
        },
        "difficultyMultiplier": {"type": "number", "minimum": 1.0, "maximum": 3.0},
        "type": {"type": "string", "enum": ["coding", "debugging", "mcq"]}
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# System Prompts (Optimized for GPT-OSS-20B)
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert computer science educator and curriculum designer.
Your task is to generate high-quality, educational programming challenges.

CRITICAL REQUIREMENTS:
1. ALWAYS respond with VALID JSON only
2. NEVER include markdown formatting (no ```json, no backticks)
3. NEVER include explanatory text before or after the JSON
4. Follow the exact schema provided in the user prompt
5. If you cannot generate valid JSON, return an error object instead

OUTPUT FORMAT:
- Single JSON object
- No markdown wrappers
- No additional text
- All required fields must be present
- All values must match the specified types

Your goal is to create engaging, educational challenges that help developers
learn and practice programming concepts effectively."""


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Templates
# ─────────────────────────────────────────────────────────────────────────────

PROMPT_TEMPLATES = {
    "coding": """Generate a coding challenge for: {skill_title}

Skill Description: {skill_description}
Difficulty Level: {difficulty}/5
Topic: {topic_hint}

REQUIREMENTS:
1. Title: 5-10 words, specific and engaging (no generic names)
2. Description: 3-5 sentences with concrete example
3. Objectives: 1-3 clear learning objectives
4. Skills Gained: 1-3 specific skills
5. Prerequisites: 0-3 required skills
6. Completion Criteria: 1-3 measurable criteria
7. Resources: 0-5 helpful resources
8. Starter Code: Python with TODO comments
9. Test Cases: 3-5 test cases with input/output pairs
10. XP Reward: {xp_range} based on difficulty
11. Estimated Time: 15-30 minutes
12. Difficulty Multiplier: {difficulty_multiplier}

JSON SCHEMA:
{{
    "title": "Specific, Engaging Title",
    "description": "Full problem statement with example",
    "difficulty": {difficulty},
    "xpReward": {xp_min},
    "estimatedTime": "20 minutes",
    "objectives": ["Objective 1", "Objective 2"],
    "skillsGained": ["Skill 1", "Skill 2"],
    "prerequisites": ["Prerequisite 1"],
    "completionCriteria": ["Criterion 1", "Criterion 2"],
    "resources": ["Resource 1"],
    "starterCode": "def solve():\\n    # TODO: Implement this function\\n    pass",
    "testCases": [
        {{"input": "test_input", "expectedOutput": "expected_output", "hint": "Hint text"}},
        ...
    ],
    "difficultyMultiplier": {difficulty_multiplier},
    "type": "coding"
}}

IMPORTANT: Return ONLY the JSON object. No markdown, no extra text.""",

    "debugging": """Generate a debugging challenge for: {skill_title}

Skill Description: {skill_description}
Difficulty Level: {difficulty}/5
Topic: {topic_hint}

REQUIREMENTS:
1. Title: 5-10 words, specific and engaging
2. Description: Clear debugging task with buggy code description
3. Objectives: 1-3 clear debugging objectives
4. Skills Gained: 1-3 specific debugging skills
5. Prerequisites: 0-3 required skills
6. Completion Criteria: 1-3 measurable criteria
7. Resources: 0-5 helpful resources
8. Starter Code: Python with 2-3 intentional bugs
9. Test Cases: 3-5 test cases to verify the fix
10. XP Reward: {xp_range} based on difficulty
11. Estimated Time: 15-30 minutes
12. Difficulty Multiplier: {difficulty_multiplier}

JSON SCHEMA:
{{
    "title": "Debug This Bug",
    "description": "Problem description and debugging task",
    "difficulty": {difficulty},
    "xpReward": {xp_min},
    "estimatedTime": "20 minutes",
    "objectives": ["Objective 1", "Objective 2"],
    "skillsGained": ["Debugging Skill 1", "Debugging Skill 2"],
    "prerequisites": ["Prerequisite 1"],
    "completionCriteria": ["Criterion 1", "Criterion 2"],
    "resources": ["Resource 1"],
    "starterCode": "def buggy_function():\\n    # Has 2-3 bugs\\n    pass",
    "testCases": [
        {{"input": "test_input", "expectedOutput": "expected_output", "hint": "Hint text"}},
        ...
    ],
    "difficultyMultiplier": {difficulty_multiplier},
    "type": "debugging"
}}

IMPORTANT: Return ONLY the JSON object. No markdown, no extra text.""",

    "mcq": """Generate a multiple-choice question for: {skill_title}

Skill Description: {skill_description}
Difficulty Level: {difficulty}/5
Topic: {topic_hint}

REQUIREMENTS:
1. Title: 5-10 words, specific and engaging
2. Description: Clear question about the skill
3. Objectives: 1 clear learning objective
4. Skills Gained: 1 specific skill
5. Prerequisites: 0-2 required skills
6. Completion Criteria: 1 measurable criterion
7. Resources: 0-3 helpful resources
8. Options: Exactly 4 options (A, B, C, D)
9. Correct Answer: 0-3 (index of correct option)
10. Explanation: Why the correct answer is correct
11. XP Reward: {xp_range} based on difficulty
12. Estimated Time: 5-10 minutes
13. Difficulty Multiplier: {difficulty_multiplier}

JSON SCHEMA:
{{
    "title": "Multiple Choice Question",
    "description": "Question text",
    "difficulty": {difficulty},
    "xpReward": {xp_min},
    "estimatedTime": "7 minutes",
    "objectives": ["Objective 1"],
    "skillsGained": ["Skill 1"],
    "prerequisites": ["Prerequisite 1"],
    "completionCriteria": ["Criterion 1"],
    "resources": ["Resource 1"],
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correctAnswer": 0,
    "explanation": "Why this is correct",
    "testCases": [],
    "difficultyMultiplier": {difficulty_multiplier},
    "type": "mcq"
}}

IMPORTANT: Return ONLY the JSON object. No markdown, no extra text."""
}


# ─────────────────────────────────────────────────────────────────────────────
# Quest Generator Service
# ─────────────────────────────────────────────────────────────────────────────

class QuestGeneratorService:
    """
    Robust quest generation service with:
    - Strong system prompts
    - JSON schema validation
    - Output repair layer
    - Retry mechanism
    - Fallback generation
    """
    
    def __init__(self):
        """Initialize quest generator service."""
        self.lm = lm_client
        self.max_retries = getattr(settings, 'LM_STUDIO_MAX_RETRIES', 2)
        self.retry_delay = getattr(settings, 'LM_STUDIO_RETRY_DELAY', 5)
        self.cache_ttl = 3600  # 1 hour cache for generated quests
        
        # Cache for generated prompts to avoid regenerating
        self._prompt_cache: Dict[str, str] = {}
    
    def generate_quest(
        self,
        skill_title: str,
        skill_description: str,
        difficulty: int,
        topic_hint: str,
        quest_type: str
    ) -> Dict[str, Any]:
        """
        Generate a complete quest with all required fields.
        
        Args:
            skill_title: Title of the skill
            skill_description: Description of the skill
            difficulty: Difficulty level (1-5)
            topic_hint: Topic hint for quest generation
            quest_type: Type of quest (coding, debugging, mcq)
            
        Returns:
            Complete quest dictionary with all required fields
            
        Raises:
            ExecutionServiceUnavailable: If LM Studio is unavailable
            ValueError: If quest generation fails after retries
        """
        if not 1 <= difficulty <= 5:
            raise ValueError("Difficulty must be between 1 and 5")
        
        if quest_type not in ['coding', 'debugging', 'mcq']:
            raise ValueError(f"Invalid quest_type: {quest_type}")
        
        # Check cache first
        cache_key = f"quest_gen:{skill_title}:{difficulty}:{quest_type}:{topic_hint}"
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for quest: {skill_title}")
            return cached
        
        # Build prompt
        prompt = self._build_prompt(
            skill_title, skill_description, difficulty, topic_hint, quest_type
        )
        
        # Generate with retries
        quest_data = None
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                quest_data = self._generate_with_retry(prompt, attempt)
                if quest_data:
                    break
            except Exception as e:
                last_error = e
                logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
        
        if not quest_data:
            # Fallback generation
            logger.warning("All generation attempts failed, using fallback")
            quest_data = self._generate_fallback(
                skill_title, difficulty, quest_type, topic_hint
            )
        
        # Validate quest data
        quest_data = self._validate_and_fix_quest(quest_data, quest_type)
        
        # Cache the result
        cache.set(cache_key, quest_data, self.cache_ttl)
        
        return quest_data
    
    def _build_prompt(
        self,
        skill_title: str,
        skill_description: str,
        difficulty: int,
        topic_hint: str,
        quest_type: str
    ) -> str:
        """Build prompt for quest generation."""
        xp_range_map = {
            1: "100-150",
            2: "150-250",
            3: "250-350",
            4: "350-450",
            5: "450-500"
        }
        
        xp_range = xp_range_map[difficulty]
        xp_min = int(xp_range.split('-')[0])
        difficulty_multiplier = difficulty / 2.5  # Scale 0.4-2.0
        
        template = PROMPT_TEMPLATES[quest_type]
        
        return template.format(
            skill_title=skill_title,
            skill_description=skill_description,
            difficulty=difficulty,
            topic_hint=topic_hint,
            xp_range=xp_range,
            xp_min=xp_min,
            difficulty_multiplier=round(difficulty_multiplier, 1)
        )
    
    def _generate_with_retry(self, prompt: str, attempt: int) -> Optional[Dict]:
        """Generate quest with retry logic."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.lm.chat_completion(
                messages=messages,
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for more deterministic output
                response_format={"type": "json_object"}
            )
            
            content = self.lm.extract_content(response)
            logger.debug(f"Raw LM response (attempt {attempt + 1}): {content[:200]}...")
            
            # Parse JSON
            quest_data = self._parse_json_response(content)
            
            if quest_data:
                logger.info(f"Successfully generated quest on attempt {attempt + 1}")
                return quest_data
            
            return None
            
        except ExecutionServiceUnavailable as e:
            logger.error(f"LM Studio unavailable: {e}")
            raise
        except Exception as e:
            logger.warning(f"Failed to parse response on attempt {attempt + 1}: {e}")
            return None
    
    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Parse JSON from LM Studio response with repair logic."""
        try:
            # Try direct JSON parse first
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to extract JSON from any code block
        json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to extract JSON from curly braces
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Try repair
        repaired = self._repair_json(content)
        if repaired:
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass
        
        logger.error(f"Failed to parse JSON from content: {content[:500]}...")
        return None
    
    def _repair_json(self, content: str) -> Optional[str]:
        """Attempt to repair malformed JSON."""
        # Remove common issues
        repaired = content
        
        # Remove markdown markers
        repaired = re.sub(r'```json\s*', '', repaired)
        repaired = re.sub(r'```\s*', '', repaired)
        repaired = re.sub(r'^[^{]*', '', repaired, count=1)
        repaired = re.sub(r'[^}]*$', '', repaired, count=1)
        
        # Fix common JSON issues
        repaired = re.sub(r'(\w+)\s*:\s*([^"\[{])', r'"\1": \2', repaired)  # Unquoted keys
        repaired = re.sub(r'([^"\]}]),\s*}', r'\1}', repaired)  # Trailing commas
        repaired = re.sub(r'([^"\[{]),\s*]', r'\1]', repaired)  # Trailing commas in arrays
        
        return repaired if repaired else None
    
    def _validate_and_fix_quest(self, quest_data: Dict, quest_type: str) -> Dict:
        """Validate and fix quest data to match schema."""
        # Ensure all required fields exist
        required_fields = {
            'title': quest_data.get('title', 'Untitled Quest'),
            'description': quest_data.get('description', 'A programming challenge'),
            'difficulty': quest_data.get('difficulty', 1),
            'xpReward': quest_data.get('xpReward', 100),
            'estimatedTime': quest_data.get('estimatedTime', '15 minutes'),
            'objectives': quest_data.get('objectives', ['Learn the topic']),
            'skillsGained': quest_data.get('skillsGained', ['Programming skills']),
            'prerequisites': quest_data.get('prerequisites', []),
            'completionCriteria': quest_data.get('completionCriteria', ['Pass all test cases']),
            'resources': quest_data.get('resources', []),
            'starterCode': quest_data.get('starterCode', 'def solve():\n    pass'),
            'testCases': quest_data.get('testCases', []),
            'difficultyMultiplier': quest_data.get('difficultyMultiplier', 1.0),
            'type': quest_type
        }
        
        # Ensure test cases have correct structure
        test_cases = required_fields['testCases']
        if not isinstance(test_cases, list) or len(test_cases) < 3:
            # Generate default test cases
            test_cases = [
                {
                    "input": "test_input_1",
                    "expectedOutput": "expected_output_1",
                    "hint": "Hint for test case 1"
                },
                {
                    "input": "test_input_2",
                    "expectedOutput": "expected_output_2",
                    "hint": "Hint for test case 2"
                },
                {
                    "input": "test_input_3",
                    "expectedOutput": "expected_output_3",
                    "hint": "Hint for test case 3"
                }
            ]
        
        # Ensure test cases have required fields
        for tc in test_cases:
            if 'input' not in tc:
                tc['input'] = 'default_input'
            if 'expectedOutput' not in tc:
                tc['expectedOutput'] = 'default_output'
            if 'hint' not in tc:
                tc['hint'] = 'Hint not available'
        
        required_fields['testCases'] = test_cases
        
        # Validate and fix numeric fields
        required_fields['difficulty'] = max(1, min(5, int(required_fields['difficulty'])))
        required_fields['xpReward'] = max(100, min(500, int(required_fields['xpReward'])))
        required_fields['difficultyMultiplier'] = max(1.0, min(3.0, float(required_fields['difficultyMultiplier'])))
        
        return required_fields
    
    def _generate_fallback(
        self,
        skill_title: str,
        difficulty: int,
        quest_type: str,
        topic_hint: str
    ) -> Dict[str, Any]:
        """Generate fallback quest when AI is unavailable."""
        logger.info(f"Using fallback generation for: {skill_title}")
        
        xp_range_map = {
            1: (100, 150),
            2: (150, 250),
            3: (250, 350),
            4: (350, 450),
            5: (450, 500)
        }
        
        xp_min, xp_max = xp_range_map[difficulty]
        xp_reward = (xp_min + xp_max) // 2
        
        difficulty_multiplier = difficulty / 2.5
        
        if quest_type == 'coding':
            return {
                "title": f"{topic_hint or 'Programming'} Challenge",
                "description": f"Create a program that demonstrates {topic_hint or 'the skill'} at {difficulty}/5 difficulty level. This challenge will help you practice and master the concepts.",
                "difficulty": difficulty,
                "xpReward": xp_reward,
                "estimatedTime": f"{15 + difficulty * 5} minutes",
                "objectives": [
                    f"Understand {topic_hint or 'the core concepts'}",
                    "Implement a working solution",
                    "Pass all test cases"
                ],
                "skillsGained": [
                    f"Programming with {topic_hint or 'the skill'}",
                    "Problem solving",
                    "Code testing"
                ],
                "prerequisites": [],
                "completionCriteria": [
                    "All test cases pass",
                    "Code follows best practices"
                ],
                "resources": [
                    "Documentation",
                    "Code examples",
                    "Community forums"
                ],
                "starterCode": f"def solve():\n    # TODO: Implement {topic_hint or 'the solution'}\n    pass",
                "testCases": [
                    {"input": "test1", "expectedOutput": "result1", "hint": "Start with basic case"},
                    {"input": "test2", "expectedOutput": "result2", "hint": "Consider edge cases"},
                    {"input": "test3", "expectedOutput": "result3", "hint": "Test error handling"}
                ],
                "difficultyMultiplier": round(difficulty_multiplier, 1),
                "type": "coding"
            }
        
        elif quest_type == 'debugging':
            return {
                "title": f"Debug the {topic_hint or 'Code'}",
                "description": f"Fix bugs in the provided code that demonstrates {topic_hint or 'the skill'} at {difficulty}/5 difficulty level. Identify and correct all issues.",
                "difficulty": difficulty,
                "xpReward": xp_reward,
                "estimatedTime": f"{15 + difficulty * 5} minutes",
                "objectives": [
                    f"Identify bugs in {topic_hint or 'the code'}",
                    "Fix all issues",
                    "Pass all test cases"
                ],
                "skillsGained": [
                    f"Debugging {topic_hint or 'the skill'}",
                    "Code analysis",
                    "Problem diagnosis"
                ],
                "prerequisites": [],
                "completionCriteria": [
                    "All test cases pass",
                    "No bugs remain"
                ],
                "resources": [
                    "Debugging guide",
                    "Error messages reference",
                    "Code review tips"
                ],
                "starterCode": f"def buggy_function():\n    # TODO: Fix the bugs in this code\n    pass",
                "testCases": [
                    {"input": "test1", "expectedOutput": "result1", "hint": "Check for syntax errors"},
                    {"input": "test2", "expectedOutput": "result2", "hint": "Verify logic flow"},
                    {"input": "test3", "expectedOutput": "result3", "hint": "Test edge cases"}
                ],
                "difficultyMultiplier": round(difficulty_multiplier, 1),
                "type": "debugging"
            }
        
        else:  # mcq
            return {
                "title": f"{topic_hint or 'Knowledge Check'} Quiz",
                "description": f"Test your understanding of {topic_hint or 'the skill'} with this multiple-choice question at {difficulty}/5 difficulty level.",
                "difficulty": difficulty,
                "xpReward": xp_reward,
                "estimatedTime": "5 minutes",
                "objectives": [
                    f"Assess understanding of {topic_hint or 'the topic'}"
                ],
                "skillsGained": [
                    f"Conceptual understanding of {topic_hint or 'the skill'}"
                ],
                "prerequisites": [],
                "completionCriteria": [
                    "Select correct answer"
                ],
                "resources": [
                    "Topic documentation",
                    "Study guide"
                ],
                "options": [
                    f"Option A: Correct answer for {topic_hint or 'the question'}",
                    "Option B: Plausible but incorrect",
                    "Option C: Plausible but incorrect",
                    "Option D: Plausible but incorrect"
                ],
                "correctAnswer": 0,
                "explanation": "This is the correct answer because it best addresses the question.",
                "testCases": [],
                "difficultyMultiplier": round(difficulty_multiplier, 1),
                "type": "mcq"
            }
    
    def generate_batch_quests(
        self,
        skill_title: str,
        skill_description: str,
        difficulty: int,
        topic_hint: str,
        quest_type: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple quests.
        
        Args:
            skill_title: Title of the skill
            skill_description: Description of the skill
            difficulty: Difficulty level (1-5)
            topic_hint: Topic hint for quest generation
            quest_type: Type of quest
            count: Number of quests to generate (1-10)
            
        Returns:
            List of quest dictionaries
        """
        if not 1 <= count <= 10:
            raise ValueError("Count must be between 1 and 10")
        
        quests = []
        for i in range(count):
            try:
                quest = self.generate_quest(
                    skill_title, skill_description, difficulty, 
                    f"{topic_hint} (variant {i+1})", quest_type
                )
                quests.append(quest)
            except Exception as e:
                logger.error(f"Failed to generate quest {i+1}: {e}")
                # Add fallback quest
                quest = self._generate_fallback(
                    skill_title, difficulty, quest_type, 
                    f"{topic_hint} (variant {i+1})"
                )
                quests.append(quest)
        
        return quests


# Singleton instance
quest_generator = QuestGeneratorService()
