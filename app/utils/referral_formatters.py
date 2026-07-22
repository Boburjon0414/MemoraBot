"""Text formatters for referral & coin pages (user-facing and admin).

V1.5: All hardcoded strings replaced with t() calls.
All public functions accept `lang: str = "uz"`.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.database.models.coin_transaction import CoinTransaction
from app.database.models.referral import Referral
from app.texts.messages import t


# ── Helpers ────────────────────────────────────────────────────────────────


def _fmt_date(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%d.%m.%Y")


def _tx_label(tx_type: str, lang: str = "uz") -> str:
    """Return a localised label for a CoinTransaction type."""
    key_map = {
        "referral": "coins.tx.referral",
        "welcome_bonus": "coins.tx.welcome_bonus",
        "admin_add": "coins.tx.admin_add",
        "admin_remove": "coins.tx.admin_remove",
        "admin_reset": "coins.tx.admin_reset",
        "bonus": "coins.tx.bonus",
        "premium_redeem": "coins.tx.premium_redeem",
    }
    key = key_map.get(tx_type)
    return t(key, lang) if key else tx_type.replace("_", " ").title()


# ── User-facing formatters ─────────────────────────────────────────────────


def format_invite_friends_page(stats: dict, lang: str = "uz") -> str:
    """Render the full invite-friends page from `ReferralService.get_invite_stats()`."""
    balance: int = stats["balance"]
    referral_count: int = stats["referral_count"]
    next_reward: int = stats["next_reward"]
    invite_link: str = stats["invite_link"]
    milestone: dict = stats["milestone"]

    lines = [
        t("referral.invite.title", lang),
        "",
        t("referral.invite.tagline", lang),
        "",
        t("referral.invite.balance", lang, balance=str(balance)),
        t("referral.invite.count", lang, count=str(referral_count)),
        t("referral.invite.next_reward", lang, reward=str(next_reward)),
        "",
        t("referral.invite.link", lang),
        f"<code>{invite_link}</code>",
        "",
        "─" * 32,
    ]

    if milestone["can_afford"]:
        lines += [
            t("referral.milestone.congrats", lang),
            "",
            t("referral.milestone.can_afford", lang, cost=str(milestone["premium_cost"])),
        ]
    else:
        fn: int = milestone["friends_needed"]
        cn: int = milestone["coins_needed"]
        cr: int = milestone["coins_from_referrals"]
        pc: int = milestone["premium_cost"]

        friends_key = "referral.milestone.friends_one" if fn == 1 else "referral.milestone.friends_many"
        friends_text = t(friends_key, lang, n=str(fn))

        lines += [
            t("referral.milestone.goal_title", lang),
            "",
            friends_text,
            t("referral.milestone.coins_needed", lang, coins=str(cn), cost=str(pc)),
            t("referral.milestone.referral_earn", lang, n=str(fn), coins=str(cr)),
            "",
            t("referral.milestone.cta", lang),
        ]

    return "\n".join(lines)


def format_coin_history_page(
    stats: dict,
    txs: list[CoinTransaction],
    lang: str = "uz",
) -> str:
    """Render the coin-history page."""
    balance: int = stats["balance"]
    earned: int = stats["lifetime_earned"]
    spent: int = stats["lifetime_spent"]

    lines = [
        t("coins.history.title", lang),
        "",
        t("coins.history.balance", lang, balance=str(balance)),
        t("coins.history.earned", lang, earned=str(earned)),
        t("coins.history.spent", lang, spent=str(spent)),
        "",
        "─" * 32,
        t("coins.history.recent", lang),
        "",
    ]

    if not txs:
        lines.append(t("coins.history.empty", lang))
    else:
        for tx in txs:
            sign = "+" if tx.amount > 0 else ""
            emoji = "📥" if tx.amount > 0 else "📤"
            date_str = _fmt_date(tx.created_at)
            label = _tx_label(tx.tx_type, lang)
            lines.append(
                f"{emoji} <b>{sign}{tx.amount} 🪙</b>  {label}  "
                f"<i>({date_str})</i>"
            )

    return "\n".join(lines)


# ── Admin formatters ───────────────────────────────────────────────────────


def format_top_referrers(rows: list[dict], lang: str = "uz") -> str:
    if not rows:
        return (
            t("admin.referral.top_referrers.title", lang) + "\n\n"
            + t("admin.referral.top_referrers.empty", lang)
        )

    invites_label = t("admin.referral.top_referrers.invites", lang)
    earned_label = t("admin.referral.top_referrers.earned", lang)
    balance_label = t("admin.referral.top_referrers.balance", lang)

    lines = [t("admin.referral.top_referrers.title", lang), ""]
    for i, row in enumerate(rows, 1):
        user = row["user"]
        uname = f"@{user.username}" if user.username else "—"
        lines.append(
            f"{i}. <b>{user.full_name}</b> ({uname})\n"
            f"   ID: <code>{user.telegram_id}</code>\n"
            f"   👥 {row['referral_count']} {invites_label}  |  "
            f"💰 {earned_label}: {row['coins_earned']}  |  "
            f"🪙 {balance_label}: {row['current_balance']}\n"
        )
    return "\n".join(lines)


def format_top_coin_holders(rows: list[dict], lang: str = "uz") -> str:
    if not rows:
        return (
            t("admin.referral.top_holders.title", lang) + "\n\n"
            + t("admin.referral.top_holders.empty", lang)
        )

    invites_label = t("admin.referral.top_holders.invites", lang)
    lines = [t("admin.referral.top_holders.title", lang), ""]
    for i, row in enumerate(rows, 1):
        user = row["user"]
        wallet = row["wallet"]
        uname = f"@{user.username}" if user.username else "—"
        lines.append(
            f"{i}. <b>{user.full_name}</b> ({uname})\n"
            f"   ID: <code>{user.telegram_id}</code>\n"
            f"   🪙 {wallet.coin_balance}  |  "
            f"📈 {wallet.lifetime_earned}  |  "
            f"👥 {invites_label}: {row['referral_count']}\n"
        )
    return "\n".join(lines)


def format_recent_referrals(rows: list[Referral], lang: str = "uz") -> str:
    if not rows:
        return (
            t("admin.referral.recent.title", lang) + "\n\n"
            + t("admin.referral.recent.empty", lang)
        )

    lines = [t("admin.referral.recent.title", lang), ""]
    for row in rows:
        ref_name = row.referrer.full_name if row.referrer else "?"
        new_name = row.referred.full_name if row.referred else "?"
        date_str = _fmt_date(row.created_at)
        lines.append(
            f"👤 <b>{ref_name}</b> → <b>{new_name}</b>\n"
            f"   🪙 +{row.reward_amount}  |  📅 {date_str}\n"
        )
    return "\n".join(lines)


def format_referral_stats(stats: dict, lang: str = "uz") -> str:
    return "\n".join([
        t("admin.referral.stats.title", lang),
        "",
        t("admin.referral.stats.total", lang, value=str(stats["total_referrals"])),
        t("admin.referral.stats.unique", lang, value=str(stats["unique_referrers"])),
        t("admin.referral.stats.total_coins", lang, value=str(stats["total_coins_awarded"])),
        "",
        t("admin.referral.stats.circulation", lang, value=str(stats["coins_in_circulation"])),
        t("admin.referral.stats.ever_earned", lang, value=str(stats["coins_ever_earned"])),
    ])


def format_user_admin_profile(profile: dict, lang: str = "uz") -> str:
    user = profile["user"]
    wallet = profile["wallet"]
    referrer = profile["referrer"]
    invited = profile["invited_count"]
    is_premium = profile["is_premium"]
    recent_tx: list[CoinTransaction] = profile["recent_tx"]

    uname = f"@{user.username}" if user.username else "—"
    ref_str = (
        f"@{referrer.username} ({referrer.full_name})"
        if referrer and referrer.username
        else (referrer.full_name if referrer else t("admin.referral.profile.no_referrer", lang))
    )
    premium_str = (
        t("admin.referral.profile.premium_yes", lang)
        if is_premium
        else t("admin.referral.profile.premium_no", lang)
    )
    reg_date = _fmt_date(user.created_at)

    lines = [
        f"👤 <b>{user.full_name}</b>  ({uname})",
        f"🆔 <code>{user.telegram_id}</code>",
        t("admin.referral.profile.reg_date", lang, date=reg_date),
        t("admin.referral.profile.premium_label", lang, value=premium_str),
        "",
        t("admin.referral.profile.coin_balance", lang, value=str(wallet.coin_balance)),
        t("admin.referral.profile.lifetime_earned", lang, value=str(wallet.lifetime_earned)),
        t("admin.referral.profile.lifetime_spent", lang, value=str(wallet.lifetime_spent)),
        "",
        t("admin.referral.profile.invites", lang, value=str(invited)),
        t("admin.referral.profile.referrer", lang, value=ref_str),
        t("admin.referral.profile.referral_code", lang, value=wallet.referral_code),
    ]

    if recent_tx:
        lines += ["", t("admin.referral.profile.recent_tx_title", lang)]
        for tx in recent_tx:
            sign = "+" if tx.amount > 0 else ""
            label = _tx_label(tx.tx_type, lang)
            lines.append(f"  {sign}{tx.amount} 🪙  {label}")

    return "\n".join(lines)
