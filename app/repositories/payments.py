from typing import Any

from app.db import get_conn

_ALLOWED_SORT_COLS = {"id", "amount", "status", "datetime"}


class PaymentRepository:
    """Data-access helper for *payments* plus a helper to pull basic user info."""

    def list_for_user(
            self,
            user_id: int,
            *,
            sort_by: str = "datetime",
            order: str = "desc",
    ) -> list[tuple[Any, ...]]:
        sort_col = sort_by if sort_by in _ALLOWED_SORT_COLS else "datetime"
        order_sql = "ASC" if order == "asc" else "DESC"

        sql = f"""
            SELECT id, user_id, amount, status, datetime
            FROM   payments
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
                       telegram_id,
                       first_name,
                       last_name,
                       username
                FROM   users
                WHERE  id = %s
                """,
                (user_id,),
            )
            return cur.fetchone()

    def total_successful(self) -> float:
        """
        Return the sum of *amount* for payments whose status is 'paid'.

        • Case-insensitive match – works with 'PAID', 'Paid', etc.
        • Falls back to 0 when no rows are found.
        """

        with get_conn() as (_, cur):
            cur.execute(
                "SELECT COALESCE(SUM(amount), 0) "
                "FROM   payments "
                "WHERE  LOWER(status) = 'paid'"
            )
        (total,) = cur.fetchone()

        return float(total)
