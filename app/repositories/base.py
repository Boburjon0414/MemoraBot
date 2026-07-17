"""Generic repository base class providing common async CRUD primitives."""

from __future__ import annotations

from typing import Generic, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository.

    Concrete repositories set the `model` class attribute and add
    domain-specific query methods on top of these shared primitives,
    satisfying the Repository Pattern while avoiding duplicated
    boilerplate (SRP + DRY).
    """

    model: Type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: int) -> ModelType | None:
        """Fetch a single row by primary key, or None if it doesn't exist."""
        return await self._session.get(self.model, entity_id)

    async def add(self, instance: ModelType) -> ModelType:
        """Add a new instance, flush it to get its generated PK, and return it."""
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Delete an instance."""
        await self._session.delete(instance)
        await self._session.flush()

    async def list_all(self) -> Sequence[ModelType]:
        """Return every row of this model. Intended for small/reference tables."""
        result = await self._session.execute(select(self.model))
        return result.scalars().all()
