"""ORM models. Importing this package registers every model on `Base.metadata`,
which is required both for `init_models()` (V1 auto-create) and for Alembic
autogenerate to see the full schema.
"""

from app.database.models.coin_transaction import CoinTransaction
from app.database.models.coin_wallet import CoinWallet
from app.database.models.content_chunk import ContentChunk    # Step 6
from app.database.models.content_source import ContentSource  # Step 5
from app.database.models.feature_output import FeatureOutput  # Step 7
from app.database.models.learning_activity import LearningActivity  # Step 1
from app.database.models.mnemonic_feedback import MnemonicFeedback
from app.database.models.mnemonic_history import MnemonicHistory
from app.database.models.referral import Referral
from app.database.models.user import User
from app.database.models.user_memory import UserMemory         # Step 8
from app.database.models.grammar_topic import GrammarTopic              # Feature: Grammar
from app.database.models.user_grammar_progress import UserGrammarProgress  # Feature: Grammar
from app.database.models.user_settings import UserSettings
from app.database.models.vocabulary import VocabularyEntry  # V1.6

__all__ = [
    "User",
    "MnemonicHistory",
    "UserSettings",
    "MnemonicFeedback",
    "CoinWallet",
    "CoinTransaction",
    "Referral",
    "VocabularyEntry",   # V1.6
    "LearningActivity",  # Step 1
    "ContentSource",     # Step 5
    "ContentChunk",      # Step 6
    "FeatureOutput",     # Step 7
    "UserMemory",        # Step 8
    "GrammarTopic",           # Feature: Grammar
    "UserGrammarProgress",    # Feature: Grammar
]
