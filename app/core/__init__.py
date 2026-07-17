"""Cross-cutting concerns shared by every layer: enums and exceptions.

Nothing in this package should ever import from `services`, `repositories`,
`handlers`, or `database` — it sits at the bottom of the dependency graph.
"""
