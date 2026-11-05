"""Slug generation utilities for GrammarTopic.

Generates URL-safe, database-safe slugs from human-readable topic names.
Handles collisions deterministically by appending a numeric suffix.
"""

from __future__ import annotations

import re


def generate_slug(title: str) -> str:
    """Convert a human-readable title to a URL-safe slug.

    Examples:
        "Present Perfect"      → "present-perfect"
        "Past Simple (Active)" → "past-simple-active"
        "Modal Verbs: Can/Could" → "modal-verbs-can-could"
    """
    slug = title.lower().strip()
    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)
    # Remove characters that are not alphanumeric or hyphens
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)
    # Strip leading/trailing hyphens
    slug = slug.strip("-")
    return slug or "topic"


def make_unique_slug(base_slug: str, existing_slugs: set[str]) -> str:
    """Append a numeric suffix until the slug is unique.

    Examples:
        base="present-perfect", existing={"present-perfect"}
        → "present-perfect-2"

        base="present-perfect", existing={"present-perfect", "present-perfect-2"}
        → "present-perfect-3"
    """
    if base_slug not in existing_slugs:
        return base_slug
    counter = 2
    while f"{base_slug}-{counter}" in existing_slugs:
        counter += 1
    return f"{base_slug}-{counter}"
