"""
Backward-compatibility shim.
OnboardingProfile has been consolidated into users/models.py.
All imports from this module continue to work.
"""
from users.models import OnboardingProfile  # noqa: F401

__all__ = ['OnboardingProfile']
