# app/repositories/webapp_user.py
from app.db import get_conn


_ALLOWED_SORT_COLS = {"id", "email", "balance", "total_spent"}


class WebAppUserRepository:
    """Very small helper around *webapp_users*."""

    def find_many(self, *, search: str = "", sort_by: str = "id", order: str = "asc"):
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
            WHERE  (%(search)s = ''
                    OR email ILIKE %(like)s)
            ORDER BY {sort_by} {order_sql}
        """
        params = {"search": search, "like": f"%{search}%"}
        with get_conn() as (_, cur):
            cur.execute(sql, params)
            return cur.fetchall()

    def update_balance(self, user_id: int, new_balance: float) -> None:
        with get_conn() as (_, cur):
            cur.execute(
                "UPDATE webapp_users SET balance = %s WHERE id = %s",
                (new_balance, user_id),
            )
