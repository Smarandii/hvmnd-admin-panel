from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo

from psycopg2 import sql as _psql

from app.db import get_conn
from app.repositories.tg_interactions import _pretty_type, _pretty_data

_MSK = ZoneInfo("Europe/Moscow")
_ALLOWED_SORT_COLS = {"id", "timestamp", "event_type", "username", "telegram_id"}


class AllInteractionRepository:
    """
    Aggregate view over *tg_user_interactions* for **all** Telegram users.

    Each tuple returned is:
        (interaction_id, user_id, username, telegram_id,
         event_type*, event_data*, timestamp_MSK*)
    Items marked with * are already prettified / converted to Moscow TZ.
    """

    def list_recent(
            self,
            *,
            limit: int = 500,
            sort_by: str = "timestamp",
            order: str = "desc",
    ) -> list[tuple[Any, ...]]:
        sort_col = sort_by if sort_by in _ALLOWED_SORT_COLS else "timestamp"
        order_sql = _psql.SQL("ASC") if order == "asc" else _psql.SQL("DESC")

        qry = _psql.SQL(
            """
            SELECT  i.id,
                    u.id          AS user_id,
                    COALESCE(NULLIF(u.username, ''), CONCAT('id_', u.id)) AS username,
                    i.telegram_id,
                    i.event_type,
                    i.event_data,
                    i.timestamp   -- timestamptz (UTC)
            FROM    tg_user_interactions i
            JOIN    users               u ON u.telegram_id = i.telegram_id
            ORDER   BY {sort} {ord}
            LIMIT   %s
            """
        ).format(sort=_psql.Identifier(sort_col), ord=order_sql)

        with get_conn() as (_, cur):
            cur.execute(qry, (limit,))
            rows = cur.fetchall()

        return [
            (
                r[0],  # interaction id
                r[1],  # internal user id
                r[2],  # username / id_123
                r[3],  # telegram id
                _pretty_type(r[4]),  # readable event type
                _pretty_data(r[5]),  # readable event data
                r[6].astimezone(_MSK)  # Moscow time
            )
            for r in rows
        ]
