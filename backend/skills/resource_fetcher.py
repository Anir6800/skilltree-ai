"""
FreeResourceFetcher — SkillTree AI
====================================
Fetches FREE learning resources (YouTube, docs, GitHub, tutorials, university
courses, blogs) for a skill topic using the SERP API (Google engine).

Also home of api_cached(): a small DB-backed cache (skills.models.APICache)
shared by this fetcher and the Apify course fetcher, so repeated generations
never re-pay for the same external API call.
"""

import logging
from datetime import timedelta
from typing import Callable, Dict, List

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

CACHE_TTL = timedelta(days=14)
_SERP_ENDPOINT = "https://serpapi.com/search.json"


def api_cached(key: str, fetch_fn: Callable[[], list]) -> list:
    """
    Return cached payload for `key` if fresher than CACHE_TTL, else call
    fetch_fn(), cache a non-empty result, and return it.
    Empty results are NOT cached so transient API failures retry next time.
    """
    from skills.models import APICache

    cutoff = timezone.now() - CACHE_TTL
    hit = APICache.objects.filter(key=key, created_at__gte=cutoff).first()
    if hit is not None:
        logger.debug("[CACHE] hit for %s", key)
        return hit.payload

    payload = fetch_fn()
    if payload:
        APICache.objects.update_or_create(
            key=key,
            defaults={"payload": payload, "created_at": timezone.now()},
        )
    return payload


class FreeResourceFetcher:
    """
    Fetches free learning resources for a skill via SERP API Google search.
    Gracefully returns [] when SERP_API_KEY is missing or the API fails.
    """

    def __init__(self):
        self._key: str = getattr(settings, "SERP_API_KEY", "")

    def fetch_free_resources(self, skill_title: str, max_results: int = 6) -> List[Dict]:
        """
        Return up to max_results free resources:
        {title, url, type, source, snippet}
        type ∈ youtube | documentation | github | university | tutorial
        """
        if not self._key:
            logger.warning("[RESOURCES] SERP_API_KEY not set — skipping free resources for %r", skill_title)
            return []

        query = f"{skill_title} free tutorial OR documentation OR course OR github"
        results = self._search(query, num=10)

        # Guarantee video content: if nothing from YouTube came back, run one
        # targeted query for playlists.
        if not any(r["type"] == "youtube" for r in results):
            results.extend(self._search(f"{skill_title} playlist site:youtube.com", num=3))

        # De-dupe by URL, keep order
        seen, unique = set(), []
        for r in results:
            if r["url"] not in seen:
                seen.add(r["url"])
                unique.append(r)
        return unique[:max_results]

    # ------------------------------------------------------------------

    def _search(self, query: str, num: int) -> List[Dict]:
        try:
            resp = requests.get(
                _SERP_ENDPOINT,
                params={"engine": "google", "q": query, "num": num, "api_key": self._key},
                timeout=20,
            )
            resp.raise_for_status()
            items = resp.json().get("organic_results", [])
        except Exception as exc:
            logger.warning("[RESOURCES] SERP search failed for %r: %s", query, exc)
            return []

        out = []
        for item in items:
            url = item.get("link") or ""
            if not url:
                continue
            out.append({
                "title": item.get("title") or url,
                "url": url,
                "type": self._classify(url),
                "source": item.get("source") or "",
                "snippet": item.get("snippet") or "",
            })
        return out

    @staticmethod
    def _classify(url: str) -> str:
        u = url.lower()
        if "youtube.com" in u or "youtu.be" in u:
            return "youtube"
        if "github.com" in u:
            return "github"
        if any(s in u for s in ("docs.", "/docs", "documentation", "readthedocs", "developer.mozilla")):
            return "documentation"
        if any(s in u for s in (".edu", "ocw.mit", "coursera.org", "edx.org", "khanacademy")):
            return "university"
        return "tutorial"
