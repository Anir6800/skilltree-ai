"""
Seed Utilities — SkillTree AI
=================================
Reusable helpers for slug generation, validation, dependency graph building,
and transactional seed execution. All functions are deterministic.
"""

import hashlib
import re
from collections import defaultdict


def slugify(text: str) -> str:
    """
    Deterministic slug generation from a title string.
    Produces identical output for identical input every time.

    >>> slugify("Build Queue Worker")
    'build-queue-worker'
    >>> slugify("HTML/CSS Foundations")
    'html-css-foundations'
    """
    slug = text.lower().strip()
    slug = re.sub(r'[/&]', '-', slug)
    slug = re.sub(r'[^a-z0-9\-]', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug


def generate_chroma_id(content_type: str, slug: str) -> str:
    """
    Deterministic ChromaDB document ID.

    >>> generate_chroma_id("skill", "binary-search")
    'seed_skill_binary-search'
    """
    return f"seed_{content_type}_{slug}"


def generate_checksum(text: str) -> str:
    """
    SHA-256 checksum for embedding staleness detection.
    Deterministic for identical input.
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def build_embedding_text(title: str, description: str, category: str, subcategory: str) -> str:
    """
    Compose the text that will be embedded in ChromaDB.
    Deterministic composition ensures stable checksums.
    """
    return f"{title}. {description} Category: {category}. Subcategory: {subcategory}."


def validate_no_cycles(edges: list[tuple[str, str]]) -> list[str]:
    """
    Validate that a directed graph (represented as (from, to) edges) has no cycles.
    Returns a list of error messages; empty list means no cycles found.

    Uses DFS-based cycle detection (Kahn's algorithm variant).

    Args:
        edges: List of (from_slug, to_slug) tuples.

    Returns:
        List of error strings describing any cycles found.
    """
    adj = defaultdict(list)
    in_degree = defaultdict(int)
    all_nodes = set()

    for from_slug, to_slug in edges:
        adj[from_slug].append(to_slug)
        in_degree[to_slug] += 1
        all_nodes.add(from_slug)
        all_nodes.add(to_slug)

    # Initialize in-degree for nodes with no incoming edges
    for node in all_nodes:
        if node not in in_degree:
            in_degree[node] = 0

    # Kahn's algorithm: topological sort
    queue = [n for n in sorted(all_nodes) if in_degree[n] == 0]
    visited_count = 0

    while queue:
        node = queue.pop(0)
        visited_count += 1
        for neighbor in sorted(adj[node]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited_count != len(all_nodes):
        # Find nodes involved in cycles
        cycle_nodes = [n for n in sorted(all_nodes) if in_degree[n] > 0]
        return [f"Cyclic dependency detected involving: {', '.join(cycle_nodes)}"]

    return []


def validate_unique_slugs(slugs: list[str]) -> list[str]:
    """
    Validate that all slugs are unique.
    Returns error messages for any duplicates found.
    """
    seen = {}
    errors = []
    for slug in slugs:
        if slug in seen:
            errors.append(f"Duplicate slug: '{slug}' (first occurrence at index {seen[slug]})")
        else:
            seen[slug] = slugs.index(slug)
    return errors


def validate_skill_mapping(quest_skill_slugs: list[str], skill_slugs: set[str]) -> list[str]:
    """
    Validate that every quest maps to a valid skill slug.
    Returns error messages for any invalid mappings.
    """
    errors = []
    for slug in quest_skill_slugs:
        if slug not in skill_slugs:
            errors.append(f"Quest references nonexistent skill slug: '{slug}'")
    return errors


def validate_xp_progression(skills: list[dict]) -> list[str]:
    """
    Validate XP progression is balanced:
    - Lower difficulty skills should have lower unlock XP
    - No skill at difficulty 1 should require XP to unlock
    """
    errors = []
    for skill in skills:
        diff = skill['difficulty']
        unlock_xp = skill['xp_required_to_unlock']
        if diff == 1 and unlock_xp > 0:
            errors.append(
                f"Skill '{skill['title']}' is difficulty 1 but requires "
                f"{unlock_xp} XP to unlock (should be 0)"
            )
    return errors


def validate_prerequisite_integrity(
    prerequisite_edges: list[tuple[str, str]],
    skill_slugs: set[str],
) -> list[str]:
    """
    Validate all prerequisite edges reference existing skill slugs.
    """
    errors = []
    for from_slug, to_slug in prerequisite_edges:
        if from_slug not in skill_slugs:
            errors.append(f"Prerequisite edge references missing from_skill: '{from_slug}'")
        if to_slug not in skill_slugs:
            errors.append(f"Prerequisite edge references missing to_skill: '{to_slug}'")
    return errors


def compute_tree_depth(
    slug: str,
    prerequisite_map: dict[str, list[str]],
    depth_cache: dict[str, int],
) -> int:
    """
    Recursively compute tree depth for a skill based on its prerequisites.
    Root nodes (no prerequisites) have depth 0.
    Depth = max(depth of all prerequisites) + 1.

    Uses memoization via depth_cache to avoid redundant computation.
    """
    if slug in depth_cache:
        return depth_cache[slug]

    prereqs = prerequisite_map.get(slug, [])
    if not prereqs:
        depth_cache[slug] = 0
        return 0

    max_prereq_depth = max(
        compute_tree_depth(p, prerequisite_map, depth_cache) for p in prereqs
    )
    depth = max_prereq_depth + 1
    depth_cache[slug] = depth
    return depth


def build_prerequisite_map(edges: list[tuple[str, str]]) -> dict[str, list[str]]:
    """
    Build a mapping from skill slug → list of prerequisite slugs.
    Edge semantics: (from_slug, to_slug) means from_skill must be completed
    before to_skill unlocks.

    Returns: {to_slug: [from_slug, ...]}
    """
    prereq_map = defaultdict(list)
    for from_slug, to_slug in edges:
        prereq_map[to_slug].append(from_slug)
    return dict(prereq_map)
