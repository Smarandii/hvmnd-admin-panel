# app/repositories/interaction.py
from __future__ import annotations

import re
from typing import Any
from zoneinfo import ZoneInfo
from psycopg2 import sql as _psql

from app.db import get_conn


_ALLOWED_SORT_COLS = {"id", "event_type", "timestamp"}
_MSK = ZoneInfo("Europe/Moscow")       # cached once per process


# --------------------------------------------------------------------------- #
# helpers – transform raw DB strings into human-friendly text
# --------------------------------------------------------------------------- #
_TOPUP_RX   = re.compile(r"topup_(\d+)\s+\\u20bd")          # captures amount
_YOOM_RX    = re.compile(r"check_yoomoney_payment_")       # ticket follows prefix


def _pretty_type(raw: str) -> str:
    """Map DB `event_type` → readable value."""
    return "button click" if raw == "callback_query" else raw


def _pretty_data(raw: str | None) -> str:
    """Apply all requested substitutions to `event_data`."""
    if raw is None:
        return ""

    # 1. trim surrounding quotes (if any)
    if raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1]

    # 2–5. ordered replacements
    raw = raw.replace("close_access_",   "Stop rent on ")
    raw = raw.replace("access_",         "Start rent on ")

    raw = _TOPUP_RX.sub(
        lambda m: f"Request Top Up Balance Link for {m.group(1)} ₽",
        raw,
    )

    raw = _YOOM_RX.sub(
        "Trying to check if payment was successfull. Payment ticket: ",
        raw,
    )

    return raw


# --------------------------------------------------------------------------- #
# main repository
# --------------------------------------------------------------------------- #
class InteractionRepository:
    """Thin data-access wrapper around *tg_user_interactions*."""

    # ------------------------------------------------------------------ #
    # Listing
    # ------------------------------------------------------------------ #
    def list_for_user(
        self,
        user_id: int,
        *,
        sort_by: str = "timestamp",
        order: str = "desc",
    ) -> list[tuple[Any, ...]]:
        """
        Return all interactions that belong to the Telegram user with internal
        **id = `user_id`**.  Each tuple is:

            (id, telegram_id, event_type*, event_data*, timestamp*)

        *Items marked with an asterisk are prettified for direct display.*
        """
        sort_col  = sort_by if sort_by in _ALLOWED_SORT_COLS else "timestamp"
        order_sql = _psql.SQL("ASC") if order == "asc" else _psql.SQL("DESC")

        qry = _psql.SQL(
            """
            SELECT  i.id,
                    i.telegram_id,
                    i.event_type,
                    i.event_data,
                    i.timestamp       -- timestamptz (UTC)
            FROM    tg_user_interactions  i
            JOIN    users                 u ON u.telegram_id = i.telegram_id
            WHERE   u.id = %s
            ORDER   BY {sort} {ord}
            """
        ).format(sort=_psql.Identifier(sort_col), ord=order_sql)

        with get_conn() as (_, cur):
            cur.execute(qry, (user_id,))
            rows = cur.fetchall()

        # prettify in Python (no extra SQL overhead)
        return [
            (
                row[0],                         # id
                row[1],                         # telegram_id
                _pretty_type(row[2]),           # event_type (readable)
                _pretty_data(row[3]),           # event_data (readable)
                row[4].astimezone(_MSK),        # timestamp → Moscow time
            )
            for row in rows
        ]

    # ------------------------------------------------------------------ #
    # Convenience: unchanged
    # ------------------------------------------------------------------ #
    def fetch_user_brief(self, user_id: int) -> tuple[Any, ...] | None:
        """Return `(id, telegram_id, first_name, last_name, username)`."""
        with get_conn() as (_, cur):
            cur.execute(
                """
                SELECT id, telegram_id, first_name, last_name, username
                FROM   users
                WHERE  id = %s
                """,
                (user_id,),
            )
            return cur.fetchone()
