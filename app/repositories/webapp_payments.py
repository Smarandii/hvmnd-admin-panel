from typing import Any
from app.db import get_conn
from psycopg2 import sql as _psql


_ALLOWED_SORT_COLS = {
    "id", "amount", "status", "confirmations", "created_at",
    "network_name", "token_symbol"
}


class WebAppPaymentRepository:
    """Access helper for *crypto_payment_transactions* plus joins to
       address & network for richer UI tables.
    """

    def list_for_user(
        self, user_id: int, *, sort_by: str = "created_at", order: str = "desc"
    ) -> list[tuple]:
        sort_col  = sort_by if sort_by in _ALLOWED_SORT_COLS else "created_at"
        order_sql = _psql.SQL("ASC") if order == "asc" else _psql.SQL("DESC")

        qry = _psql.SQL("""
            SELECT  t.id,
                    t.user_id,
                    t.amount,
                    t.status,
                    t.confirmations,
                    t.created_at,
                    t.transaction_hash,
                    n.name          AS network_name,
                    n.token_symbol  AS token_symbol,
                    COALESCE(d.address, '') AS deposit_address
            FROM    crypto_payment_transactions t
            LEFT JOIN crypto_networks         n ON n.id = t.network_id
            LEFT JOIN crypto_deposit_addresses d ON d.id = t.deposit_address_id
            WHERE   t.user_id = %s
            ORDER BY {sort} {ord}
        """).format(sort=_psql.Identifier(sort_col), ord=order_sql)

        with get_conn() as (_, cur):
            cur.execute(qry, (user_id,))
            return cur.fetchall()

    def fetch_user_brief(self, user_id: int) -> tuple[Any, ...] | None:
        with get_conn() as (_, cur):
            cur.execute(
                """
                SELECT id,
                       email,
                       balance,
                       total_spent
                FROM   webapp_users
                WHERE  id = %s
                """,
                (user_id,),
            )
            return cur.fetchone()
