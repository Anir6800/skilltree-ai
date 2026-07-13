"""
CourseFetcherService — SkillTree AI
=====================================
Fetches real course recommendations from Coursera and Udemy using Apify actors.
Returns up to 5 normalised course dicts per skill (3 Coursera + 2 Udemy).

SRP: This module is only responsible for course data retrieval and normalisation.
     It never touches the database directly — callers persist the result.

Apify actors used:
  Coursera: i6RB82cZTZjDXock0
  Udemy:    U8EA7UpP2GwL3WW5H
"""

import logging
from typing import Dict, List

from django.conf import settings

logger = logging.getLogger(__name__)

_COURSERA_ACTOR = "i6RB82cZTZjDXock0"
_UDEMY_ACTOR = "U8EA7UpP2GwL3WW5H"

_COURSERA_MAX = 3
_UDEMY_MAX = 2


class CourseFetcherService:
    """
    Fetches course recommendations for a skill topic from Coursera and Udemy.
    Gracefully returns [] when Apify is unavailable or the token is missing.
    """

    def __init__(self):
        self._token: str = getattr(settings, "APIFY_API_TOKEN", "")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_courses_for_skill(self, skill_title: str, max_results: int = 5) -> List[Dict]:
        """
        Fetch up to max_results courses for the given skill title.
        Returns 3 Coursera + 2 Udemy (or fewer when not enough results).

        Args:
            skill_title: Human-readable skill name used as the search query
            max_results:  Upper bound on returned courses (default 5)

        Returns:
            List of normalised course dicts:
            {title, provider, url, price, rating, instructor}
        """
        if not self._token or self._token.startswith("apify_api_REPLACE"):
            logger.warning(
                "[COURSES] APIFY_API_TOKEN not set — skipping course fetch for %r",
                skill_title,
            )
            return []

        courses: List[Dict] = []

        coursera = self._fetch_coursera(skill_title, limit=_COURSERA_MAX)
        courses.extend(coursera)

        udemy = self._fetch_udemy(skill_title, limit=_UDEMY_MAX)
        courses.extend(udemy)

        result = courses[:max_results]
        logger.info(
            "[COURSES] Fetched %d courses for %r (%d Coursera, %d Udemy)",
            len(result), skill_title, len(coursera), len(udemy),
        )
        return result

    def _get_dataset_id(self, run) -> str:
        """Safely extract defaultDatasetId from Apify Actor run (handles different Client versions)."""
        if hasattr(run, "default_dataset_id"):
            return run.default_dataset_id
        if hasattr(run, "get"):
            return run.get("defaultDatasetId") or run.get("default_dataset_id")
        try:
            return run["defaultDatasetId"]
        except Exception:
            return getattr(run, "defaultDatasetId", "")

    # ------------------------------------------------------------------
    # Private — Coursera
    # ------------------------------------------------------------------

    def _fetch_coursera(self, query: str, limit: int) -> List[Dict]:
        """Call Apify Coursera actor and return normalised results."""
        try:
            client = self._get_client()
            run_input = {
                "query": query,
                "pages": 1,
                "proxyConfiguration": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"],
                    "apifyProxyCountry": "US",
                },
            }
            run = client.actor(_COURSERA_ACTOR).call(run_input=run_input)
            dataset_id = self._get_dataset_id(run)
            items = list(client.dataset(dataset_id).iterate_items())
            return [self._normalise_coursera(item) for item in items[:limit] if item]
        except Exception as exc:
            logger.warning("[COURSES] Coursera fetch failed for %r: %s", query, exc)
            return []

    def _normalise_coursera(self, item: Dict) -> Dict:
        """Map raw Coursera actor output to our common course schema."""
        return {
            "title": item.get("name") or item.get("title") or "Unknown Course",
            "provider": "Coursera",
            "url": item.get("url") or item.get("courseUrl") or "",
            "price": item.get("pricing") or item.get("price") or "Free",
            "rating": self._safe_float(item.get("rating") or item.get("avgRating")),
            "instructor": self._extract_instructor(item.get("partners") or item.get("instructor")),
        }

    # ------------------------------------------------------------------
    # Private — Udemy
    # ------------------------------------------------------------------

    def _fetch_udemy(self, query: str, limit: int) -> List[Dict]:
        """Call Apify Udemy actor and return normalised results."""
        try:
            client = self._get_client()
            search_url = f"https://www.udemy.com/courses/search/?src=ukw&q={query.replace(' ', '+')}"
            run_input = {
                "searchUrls": [search_url],
                "maxItems": limit * 2,  # fetch extras, take best
                "proxyConfiguration": {"useApifyProxy": False},
            }
            run = client.actor(_UDEMY_ACTOR).call(run_input=run_input)
            dataset_id = self._get_dataset_id(run)
            items = list(client.dataset(dataset_id).iterate_items())
            return [self._normalise_udemy(item) for item in items[:limit] if item]
        except Exception as exc:
            logger.warning("[COURSES] Udemy fetch failed for %r: %s", query, exc)
            return []

    def _normalise_udemy(self, item: Dict) -> Dict:
        """Map raw Udemy actor output to our common course schema."""
        price = item.get("price") or item.get("discountPrice") or "Paid"
        if isinstance(price, dict):
            price = price.get("amount") or "Paid"

        return {
            "title": item.get("title") or item.get("name") or "Unknown Course",
            "provider": "Udemy",
            "url": item.get("url") or item.get("courseUrl") or "",
            "price": str(price),
            "rating": self._safe_float(item.get("rating") or item.get("avgRating")),
            "instructor": self._extract_instructor(item.get("instructors") or item.get("instructor")),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_client(self):
        """Lazily import and instantiate ApifyClient (avoids import error when not installed)."""
        try:
            from apify_client import ApifyClient
        except ImportError as exc:
            raise RuntimeError(
                "apify-client is not installed. "
                "Run: pip install apify-client"
            ) from exc
        return ApifyClient(self._token)

    @staticmethod
    def _safe_float(value) -> float:
        """Convert rating value to float, return 0.0 on failure."""
        try:
            return round(float(value), 1)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _extract_instructor(value) -> str:
        """Extract a human-readable instructor string from various API shapes."""
        if not value:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            # [{name: ...}, ...] or ["Name", ...]
            names = []
            for item in value:
                if isinstance(item, dict):
                    names.append(item.get("name") or item.get("title") or "")
                else:
                    names.append(str(item))
            return ", ".join(n for n in names if n)
        if isinstance(value, dict):
            return value.get("name") or value.get("title") or ""
        return str(value)
