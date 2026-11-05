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


class AdminReferralStates(StatesGroup):
    """States for the admin referral-control flows."""

    searching_user = State()       # waiting for Telegram ID or @username input
    waiting_coin_amount = State()  # waiting for amount (add / remove / bonus)


class VocabularyStates(StatesGroup):
    """States for the My Vocabulary search flow (V1.6)."""

    searching = State()  # waiting for the user to type a search query


class AIChatStates(StatesGroup):
    """States for the AI Chat feature (Feature A)."""

    in_session = State()  # user is mid-conversation; any text message is a chat turn


class QuizStates(StatesGroup):
    """States for the Quiz feature (Feature C)."""

    selecting_type = State()    # user chose quiz from dashboard; selecting mode
    answering = State()         # quiz is running; waiting for poll answers
    reading_passage = State()   # reading quiz: passage shown, waiting for "Start Questions"


class AdminGrammarStates(StatesGroup):
    """States for the admin Grammar Lessons management flow."""

    waiting_forward       = State()  # waiting for admin to forward channel post
    waiting_manual_msg_id = State()  # waiting for manual message_id entry
    waiting_topic_name    = State()  # waiting for topic name text
    waiting_button_name   = State()  # waiting for button name text
    confirm_delete        = State()  # waiting for delete confirmation


class GrammarStates(StatesGroup):
    """States for the Grammar Learning feature (Learn → Grammar)."""

    asking_question = State()   # user is in grammar Q&A mode; any message = grammar question
    quiz_answering  = State()   # grammar quiz in progress; waiting for poll answers
