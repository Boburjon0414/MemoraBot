"""ORM models. Importing this package registers every model on `Base.metadata`,
which is required both for `init_models()` (V1 auto-create) and for Alembic
autogenerate to see the full schema.
"""

from app.database.models.coin_transaction import CoinTransaction
from app.database.models.coin_wallet import CoinWallet
from app.database.models.mnemonic_feedback import MnemonicFeedback
from app.database.models.mnemonic_history import MnemonicHistory
from app.database.models.referral import Referral
from app.database.models.user import User
from app.database.models.user_settings import UserSettings

__all__ = [
    "User",
    "MnemonicHistory",
    "UserSettings",
    "MnemonicFeedback",
    "CoinWallet",
    "CoinTransaction",
    "Referral",
]
