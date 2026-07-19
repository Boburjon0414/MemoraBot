"""FSM state groups.

Kept together in one small file since there are only two flows in V1; split
into per-feature modules once more states are added (see README, "AI Chat").
"""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """States for the new-user registration flow (triggered by /start)."""

    waiting_for_contact = State()


class MneVocaStates(StatesGroup):
    """States for the MneVoca vocabulary-mode flow."""

    waiting_for_word = State()


class BroadcastStates(StatesGroup):
    """States for the admin broadcast composition flow."""

    waiting_for_message = State()
