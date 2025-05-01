from typing import Any
from app.db import get_conn

_ALLOWED_SORT_COLS = {"id", "email", "balance", "total_spent"}


class WebAppUserRepository:
    """Very small helper around *webapp_users*."""

    # --------------------------------------------------------------------- #
    # Listing / search
    # --------------------------------------------------------------------- #
    def find_many(self, *, search: str = "", sort_by: str = "id",
                  order: str = "asc") -> list[tuple[Any, ...]]:
        sort_by   = sort_by if sort_by in _ALLOWED_SORT_COLS else "id"
        order_sql = "ASC" if order == "asc" else "DESC"

        sql = f"""
            SELECT id,
                   email,
                   total_spent,
                   balance,
                   banned,
                   email_confirmed
            FROM   webapp_users
            WHERE  (%(search)s = '' OR email ILIKE %(like)s)
            ORDER  BY {sort_by} {order_sql}
        """
        params = {"search": search, "like": f"%{search}%"}
        with get_conn() as (_, cur):
            cur.execute(sql, params)
            return cur.fetchall()

    # --------------------------------------------------------------------- #
    # Aggregates for dashboard
    # --------------------------------------------------------------------- #
    def totals(self) -> dict[str, float]:
        """Total balance / spent across *webapp_users*."""
        with get_conn() as (_, cur):
            cur.execute("SELECT SUM(balance), SUM(total_spent) FROM webapp_users")
            bal, spent = cur.fetchone()
        return {
            "total_balance": float(bal or 0),
            "total_spent":   float(spent or 0),
        }

    def count(self) -> int:
        with get_conn() as (_, cur):
            cur.execute("SELECT COUNT(*) FROM webapp_users")
            (cnt,) = cur.fetchone()
        return int(cnt)

    # --------------------------------------------------------------------- #
    # Convenience
    # --------------------------------------------------------------------- #
    def update_balance(self, user_id: int, new_balance: float) -> None:
        with get_conn() as (_, cur):
            cur.execute(
                "UPDATE webapp_users SET balance = %s WHERE id = %s",
                (new_balance, user_id),
            )