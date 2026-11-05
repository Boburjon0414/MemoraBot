"""Per-request user learning context.

This package assembles a lightweight, immutable `UserContext` value object
once per request from existing persistent data (user_settings, vocabulary
counts, activity streak).  Every AI-calling service receives it so that
prompts can be personalised without each service independently querying
the database for the same facts.

Packages
--------
  user_context.py          — the `UserContext` dataclass (the value object)
  user_context_service.py  — `UserContextService` (assembles it from repos)

Future enrichment
-----------------
When `user_memory` is added in Step 8, `UserContextService.build()` will
populate `english_level`, `learning_goal`, and `recent_weak_words` from
that table — handlers and AI services need no changes because they already
receive a `UserContext` with those fields; they simply become non-None.
"""
