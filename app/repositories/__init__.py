"""Repository layer: async data-access classes, one per aggregate/entity.

Repositories know how to talk to SQLAlchemy; they contain zero business
logic. That belongs one layer up, in `app.services`.
"""
