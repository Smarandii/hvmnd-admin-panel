# app/repositories/webapp_payments.py
from typing import Any
from app.db import get_conn


_ALLOWED_SORT_COLS = {"id", "amount", "status", "created_at"}


class WebAppPaymentRepository:
    """Access helper for *crypto_payment_transactions* and a user brief."""

    def list_for_user(
        self, user_id: int, *, sort_by: str = "created_at", order: str = "desc"
    ) -> list[tuple[Any, ...]]:
        sort_col  = sort_by if sort_by in _ALLOWED_SORT_COLS else "created_at"
        order_sql = "ASC" if order == "asc" else "DESC"

        sql = f"""
            SELECT id, user_id, amount, status, created_at
            FROM   crypto_payment_transactions
            WHERE  user_id = %s
            ORDER  BY {sort_col} {order_sql}
        """
        with get_conn() as (_, cur):
            cur.execute(sql, (user_id,))
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
