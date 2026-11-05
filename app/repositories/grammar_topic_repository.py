"""Repository for GrammarTopic — the configurable grammar lesson catalogue."""

from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.grammar_topic import GrammarTopic
from app.repositories.base import BaseRepository


class GrammarTopicRepository(BaseRepository[GrammarTopic]):
    """CRUD + domain queries for grammar_topics."""

    model = GrammarTopic

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_active(self) -> list[GrammarTopic]:
        """Return all active topics ordered by order_index, then id."""
        result = await self._session.execute(
            select(GrammarTopic)
            .where(GrammarTopic.is_active.is_(True))
            .order_by(GrammarTopic.order_index, GrammarTopic.id)
        )
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> GrammarTopic | None:
        """Fetch one topic by its URL-safe slug."""
        result = await self._session.execute(
            select(GrammarTopic).where(GrammarTopic.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_message_id(self, channel_message_id: int) -> GrammarTopic | None:
        """Find the topic whose lesson is stored at channel_message_id."""
        result = await self._session.execute(
            select(GrammarTopic)
            .where(GrammarTopic.channel_message_id == channel_message_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        slug: str,
        title: str,
        description: str | None = None,
        channel_message_id: int = 0,
        difficulty: str | None = None,
        order_index: int = 0,
    ) -> GrammarTopic:
        """Create and persist a new GrammarTopic."""
        topic = GrammarTopic(
            slug=slug,
            title=title,
            description=description,
            channel_message_id=channel_message_id,
            difficulty=difficulty,
            order_index=order_index,
            is_active=True,
        )
        return await self.add(topic)

    async def update_channel_message(
        self, topic_id: int, channel_message_id: int
    ) -> GrammarTopic | None:
        """Update the channel message link for an existing topic."""
        topic = await self.get_by_id(topic_id)
        if topic is None:
            return None
        topic.channel_message_id = channel_message_id
        await self._session.flush()
        return topic

    async def set_active(self, topic_id: int, is_active: bool) -> GrammarTopic | None:
        """Enable or disable a topic."""
        topic = await self.get_by_id(topic_id)
        if topic is None:
            return None
        topic.is_active = is_active
        await self._session.flush()
        return topic

    async def count_active(self) -> int:
        """Return the number of active grammar topics."""
        result = await self._session.execute(
            select(func.count()).select_from(GrammarTopic)
            .where(GrammarTopic.is_active.is_(True))
        )
        return result.scalar_one()

    async def list_all(self) -> list[GrammarTopic]:
        """Return ALL topics (active and inactive) ordered by order_index, id."""
        result = await self._session.execute(
            select(GrammarTopic)
            .order_by(GrammarTopic.order_index, GrammarTopic.id)
        )
        return list(result.scalars().all())

    async def get_next_order_index(self) -> int:
        """Return max(order_index) + 1, or 0 if no topics exist yet."""
        result = await self._session.execute(
            select(func.max(GrammarTopic.order_index))
        )
        current_max = result.scalar_one_or_none()
        return (current_max + 1) if current_max is not None else 0

    async def exists_message_id(self, channel_message_id: int) -> bool:
        """Return True if any topic already uses this channel_message_id."""
        result = await self._session.execute(
            select(func.count()).select_from(GrammarTopic)
            .where(GrammarTopic.channel_message_id == channel_message_id)
        )
        return result.scalar_one() > 0

    async def exists_message_id_excluding(
        self, channel_message_id: int, exclude_topic_id: int
    ) -> bool:
        """Return True if any OTHER topic already uses this channel_message_id."""
        result = await self._session.execute(
            select(func.count()).select_from(GrammarTopic)
            .where(GrammarTopic.channel_message_id == channel_message_id)
            .where(GrammarTopic.id != exclude_topic_id)
        )
        return result.scalar_one() > 0

    async def slug_exists(self, slug: str) -> bool:
        """Return True if a topic with this slug already exists."""
        result = await self._session.execute(
            select(func.count()).select_from(GrammarTopic).where(GrammarTopic.slug == slug)
        )
        return result.scalar_one() > 0

    async def update(
        self,
        topic_id: int,
        *,
        title: str | None = None,
        button_name: str | None = ...,  # type: ignore[assignment]
        slug: str | None = None,
        channel_message_id: int | None = None,
        description: str | None = ...,  # type: ignore[assignment]
        difficulty: str | None = ...,   # type: ignore[assignment]
        order_index: int | None = None,
        is_active: bool | None = None,
    ) -> GrammarTopic | None:
        """Partial update — only updates fields that are not Ellipsis/None.

        Uses Ellipsis as sentinel for "leave unchanged" to distinguish from
        explicitly setting a field to None (which is valid for nullable fields).
        """
        topic = await self.get_by_id(topic_id)
        if topic is None:
            return None
        if title is not None:
            topic.title = title
        if button_name is not ...:
            topic.button_name = button_name
        if slug is not None:
            topic.slug = slug
        if channel_message_id is not None:
            topic.channel_message_id = channel_message_id
        if description is not ...:
            topic.description = description
        if difficulty is not ...:
            topic.difficulty = difficulty
        if order_index is not None:
            topic.order_index = order_index
        if is_active is not None:
            topic.is_active = is_active
        topic.updated_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.flush()
        return topic

    async def swap_order(self, topic_id_a: int, topic_id_b: int) -> bool:
        """Swap order_index values between two topics. Returns True on success."""
        a = await self.get_by_id(topic_id_a)
        b = await self.get_by_id(topic_id_b)
        if a is None or b is None:
            return False
        a.order_index, b.order_index = b.order_index, a.order_index
        a.updated_at = datetime.now(UTC).replace(tzinfo=None)
        b.updated_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.flush()
        return True

    async def create_full(
        self,
        *,
        slug: str,
        title: str,
        button_name: str | None = None,
        description: str | None = None,
        channel_message_id: int = 0,
        difficulty: str | None = None,
        order_index: int = 0,
    ) -> GrammarTopic:
        """Create a grammar topic with all fields including button_name."""
        topic = GrammarTopic(
            slug=slug,
            title=title,
            button_name=button_name,
            description=description,
            channel_message_id=channel_message_id,
            difficulty=difficulty,
            order_index=order_index,
            is_active=True,
        )
        return await self.add(topic)
