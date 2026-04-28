"""
Backward-compatibility shim.
AdaptiveProfile and UserSkillFlag have been consolidated into users/models.py.
All imports from this module continue to work.
"""
from users.models import AdaptiveProfile, UserSkillFlag  # noqa: F401

__all__ = ['AdaptiveProfile', 'UserSkillFlag']
