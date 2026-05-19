"""
SkillTree AI - Quest Validation Middleware
===========================================
Comprehensive validation for quest data with repair capabilities.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Quest Schema Definition
# ─────────────────────────────────────────────────────────────────────────────

QUEST_SCHEMA = {
    "required_fields": [
        "title", "description", "difficulty", "xpReward", "estimatedTime",
        "objectives", "skillsGained", "prerequisites", "completionCriteria",
        "resources", "starterCode", "testCases", "difficultyMultiplier", "type"
    ],
    "field_validators": {
        "title": {
            "type": str,
            "min_length": 5,
            "max_length": 100,
            "pattern": r"^[A-Z][^!@#$%^&*()]+$"
        },
        "description": {
            "type": str,
            "min_length": 50,
            "max_length": 2000
        },
        "difficulty": {
            "type": int,
            "min": 1,
            "max": 5
        },
        "xpReward": {
            "type": int,
            "min": 100,
            "max": 500
        },
        "estimatedTime": {
            "type": str,
            "pattern": r"^\d+\s*(minutes?|hours?)$"
        },
        "objectives": {
            "type": list,
            "min_items": 1,
            "max_items": 5,
            "item_type": str
        },
        "skillsGained": {
            "type": list,
            "min_items": 1,
            "max_items": 5,
            "item_type": str
        },
        "prerequisites": {
            "type": list,
            "min_items": 0,
            "max_items": 3,
            "item_type": str
        },
        "completionCriteria": {
            "type": list,
            "min_items": 1,
            "max_items": 5,
            "item_type": str
        },
        "resources": {
            "type": list,
            "min_items": 0,
            "max_items": 5,
            "item_type": str
        },
        "starterCode": {
            "type": str,
            "min_length": 10
        },
        "testCases": {
            "type": list,
            "min_items": 3,
            "max_items": 10,
            "item_schema": {
                "required": ["input", "expectedOutput"],
                "properties": {
                    "input": {"type": str},
                    "expectedOutput": {"type": str},
                    "hint": {"type": str}
                }
            }
        },
        "difficultyMultiplier": {
            "type": (int, float),
            "min": 1.0,
            "max": 3.0
        },
        "type": {
            "type": str,
            "enum": ["coding", "debugging", "mcq"]
        }
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# Quest Validation Service
# ─────────────────────────────────────────────────────────────────────────────

class QuestValidationService:
    """
    Comprehensive quest validation service with repair capabilities.
    """
    
    def __init__(self):
        """Initialize validation service."""
        self.schema = QUEST_SCHEMA
        self.max_retries = getattr(settings, 'LM_STUDIO_MAX_RETRIES', 2)
    
    def validate_quest(self, quest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate quest data against schema.
        
        Args:
            quest_data: Quest data dictionary
            
        Returns:
            Validated quest data with any repairs applied
            
        Raises:
            ValueError: If validation fails after repairs
        """
        if not isinstance(quest_data, dict):
            raise ValueError("Quest data must be a dictionary")
        
        # Check required fields
        missing_fields = []
        for field in self.schema["required_fields"]:
            if field not in quest_data:
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            quest_data = self._add_missing_fields(quest_data, missing_fields)
        
        # Validate each field
        errors = []
        for field, validator in self.schema["field_validators"].items():
            if field in quest_data:
                field_errors = self._validate_field(field, quest_data[field], validator)
                errors.extend(field_errors)
        
        if errors:
            logger.warning(f"Validation errors: {errors}")
            quest_data = self._repair_errors(quest_data, errors)
        
        # Final validation
        final_errors = []
        for field, validator in self.schema["field_validators"].items():
            if field in quest_data:
                field_errors = self._validate_field(field, quest_data[field], validator)
                final_errors.extend(field_errors)
        
        if final_errors:
            raise ValueError(f"Quest validation failed: {final_errors}")
        
        return quest_data
    
    def _validate_field(self, field: str, value: Any, validator: Dict) -> List[str]:
        """Validate a single field."""
        errors = []
        
        # Type check
        expected_type = validator.get("type")
        if expected_type and not isinstance(value, expected_type):
            errors.append(f"Field '{field}' must be {expected_type}, got {type(value).__name__}")
            return errors
        
        # String validators
        if isinstance(value, str):
            min_length = validator.get("min_length")
            if min_length and len(value) < min_length:
                errors.append(f"Field '{field}' must be at least {min_length} chars")
            
            max_length = validator.get("max_length")
            if max_length and len(value) > max_length:
                errors.append(f"Field '{field}' must be at most {max_length} chars")
            
            pattern = validator.get("pattern")
            if pattern and not re.match(pattern, value):
                errors.append(f"Field '{field}' doesn't match pattern {pattern}")
        
        # Numeric validators
        if isinstance(value, (int, float)):
            min_val = validator.get("min")
            if min_val is not None and value < min_val:
                errors.append(f"Field '{field}' must be >= {min_val}")
            
            max_val = validator.get("max")
            if max_val is not None and value > max_val:
                errors.append(f"Field '{field}' must be <= {max_val}")
        
        # Enum validator
        enum_values = validator.get("enum")
        if enum_values and value not in enum_values:
            errors.append(f"Field '{field}' must be one of {enum_values}")
        
        # List validators
        if isinstance(value, list):
            min_items = validator.get("min_items")
            if min_items and len(value) < min_items:
                errors.append(f"Field '{field}' must have at least {min_items} items")
            
            max_items = validator.get("max_items")
            if max_items and len(value) > max_items:
                errors.append(f"Field '{field}' must have at most {max_items} items")
            
            item_type = validator.get("item_type")
            if item_type:
                for i, item in enumerate(value):
                    if not isinstance(item, item_type):
                        errors.append(f"Field '{field}[{i}]' must be {item_type}")
            
            item_schema = validator.get("item_schema")
            if item_schema:
                for i, item in enumerate(value):
                    if not isinstance(item, dict):
                        errors.append(f"Field '{field}[{i}]' must be a dictionary")
                        continue
                    
                    required = item_schema.get("required", [])
                    for req_field in required:
                        if req_field not in item:
                            errors.append(f"Field '{field}[{i}]' missing required field '{req_field}'")
        
        return errors
    
    def _add_missing_fields(self, quest_data: Dict, missing_fields: List[str]) -> Dict:
        """Add missing fields with defaults."""
        defaults = {
            "title": "Untitled Quest",
            "description": "A programming challenge",
            "difficulty": 1,
            "xpReward": 100,
            "estimatedTime": "15 minutes",
            "objectives": ["Learn the topic"],
            "skillsGained": ["Programming skills"],
            "prerequisites": [],
            "completionCriteria": ["Pass all test cases"],
            "resources": [],
            "starterCode": "def solve():\n    pass",
            "testCases": [
                {"input": "test1", "expectedOutput": "result1", "hint": "Hint 1"},
                {"input": "test2", "expectedOutput": "result2", "hint": "Hint 2"},
                {"input": "test3", "expectedOutput": "result3", "hint": "Hint 3"}
            ],
            "difficultyMultiplier": 1.0,
            "type": "coding"
        }
        
        for field in missing_fields:
            if field in defaults:
                quest_data[field] = defaults[field]
                logger.info(f"Added missing field '{field}' with default value")
        
        return quest_data
    
    def _repair_errors(self, quest_data: Dict, errors: List[str]) -> Dict:
        """Attempt to repair validation errors."""
        repaired = quest_data.copy()
        
        for error in errors:
            # Parse error message
            if "must be" in error:
                field_match = re.match(r"Field '(\w+)' must be", error)
                if field_match:
                    field = field_match.group(1)
                    repaired = self._repair_field(repaired, field, error)
        
        return repaired
    
    def _repair_field(self, quest_data: Dict, field: str, error: str) -> Dict:
        """Repair a specific field."""
        if field == "title":
            quest_data[field] = "Untitled Quest"
        elif field == "description":
            quest_data[field] = "A programming challenge"
        elif field == "difficulty":
            quest_data[field] = 1
        elif field == "xpReward":
            quest_data[field] = 100
        elif field == "estimatedTime":
            quest_data[field] = "15 minutes"
        elif field == "objectives":
            quest_data[field] = ["Learn the topic"]
        elif field == "skillsGained":
            quest_data[field] = ["Programming skills"]
        elif field == "prerequisites":
            quest_data[field] = []
        elif field == "completionCriteria":
            quest_data[field] = ["Pass all test cases"]
        elif field == "resources":
            quest_data[field] = []
        elif field == "starterCode":
            quest_data[field] = "def solve():\n    pass"
        elif field == "testCases":
            quest_data[field] = [
                {"input": "test1", "expectedOutput": "result1", "hint": "Hint 1"},
                {"input": "test2", "expectedOutput": "result2", "hint": "Hint 2"},
                {"input": "test3", "expectedOutput": "result3", "hint": "Hint 3"}
            ]
        elif field == "difficultyMultiplier":
            quest_data[field] = 1.0
        elif field == "type":
            quest_data[field] = "coding"
        
        logger.info(f"Repaired field '{field}'")
        return quest_data
    
    def validate_and_normalize(self, quest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate quest data and normalize field names.
        
        Handles both snake_case and camelCase field names.
        
        Args:
            quest_data: Quest data dictionary
            
        Returns:
            Normalized quest data with consistent field names
        """
        normalized = {}
        
        # Field name mappings (snake_case -> camelCase)
        field_mappings = {
            "starter_code": "starterCode",
            "test_cases": "testCases",
            "xp_reward": "xpReward",
            "difficulty_multiplier": "difficultyMultiplier",
            "estimated_minutes": "estimatedTime",
            "skills_gained": "skillsGained",
            "prerequisites": "prerequisites",
            "completion_criteria": "completionCriteria",
            "learning_outcomes": "skillsGained",
            "objectives": "objectives"
        }
        
        # Normalize field names
        for key, value in quest_data.items():
            normalized_key = field_mappings.get(key, key)
            normalized[normalized_key] = value
        
        # Ensure all required fields exist
        for field in self.schema["required_fields"]:
            if field not in normalized:
                normalized[field] = self._get_default_value(field)
        
        return normalized
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for a field."""
        defaults = {
            "title": "Untitled Quest",
            "description": "A programming challenge",
            "difficulty": 1,
            "xpReward": 100,
            "estimatedTime": "15 minutes",
            "objectives": ["Learn the topic"],
            "skillsGained": ["Programming skills"],
            "prerequisites": [],
            "completionCriteria": ["Pass all test cases"],
            "resources": [],
            "starterCode": "def solve():\n    pass",
            "testCases": [
                {"input": "test1", "expectedOutput": "result1", "hint": "Hint 1"},
                {"input": "test2", "expectedOutput": "result2", "hint": "Hint 2"},
                {"input": "test3", "expectedOutput": "result3", "hint": "Hint 3"}
            ],
            "difficultyMultiplier": 1.0,
            "type": "coding"
        }
        return defaults.get(field, None)


# Singleton instance
quest_validation = QuestValidationService()
