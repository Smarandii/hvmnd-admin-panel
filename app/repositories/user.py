from typing import Any

from app.db import get_conn

# Columns that are allowed in ORDER BY
_ALLOWED_SORT_COLS = {"id", "telegram_id", "balance", "total_spent"}


class UserRepository:
    """
    Data-access helper for the *users* table.

    Adds flexible search:
      • substring match (ILIKE) on username, names, language_code, **telegram_id**
      • exact-value match on numeric fields (id, telegram_id, balance, total_spent)
    """

    # ------------------------------------------------------------------ #
    # Listing / search
    # ------------------------------------------------------------------ #
    def find_many(
            self,
            *,
            search: str = "",
            sort_by: str = "id",
            order: str = "asc",
    ) -> list[tuple[Any, ...]]:
        sort_by = sort_by if sort_by in _ALLOWED_SORT_COLS else "id"
        order_sql = "ASC" if order == "asc" else "DESC"

        # Trim leading/trailing spaces just in case
        search = search.strip()
        params = {
            "search": search,
            "like": f"%{search}%",
        }

        # If the string is a valid integer, also use equality on numeric columns
        try:
            params["num"] = int(search)
            numeric_cond = (
                " OR id = %(num)s"
                " OR telegram_id = %(num)s"
                " OR balance = %(num)s"
                " OR total_spent = %(num)s"
            )
        except ValueError:
            numeric_cond = ""

        sql = f"""
            SELECT id,
                   telegram_id,
                   total_spent,
                   balance,
                   first_name,
                   last_name,
                   username,
                   language_code
            FROM   users
            WHERE  (%(search)s = ''
                    OR username        ILIKE %(like)s
                    OR first_name      ILIKE %(like)s
                    OR last_name       ILIKE %(like)s
                    OR language_code   ILIKE %(like)s
                    OR CAST(telegram_id AS TEXT) ILIKE %(like)s
                    {numeric_cond})
            ORDER  BY {sort_by} {order_sql}
        """

        with get_conn() as (_, cur):
            cur.execute(sql, params)
            return cur.fetchall()

    # ------------------------------------------------------------------ #
    # Aggregates
    # ------------------------------------------------------------------ #
    def totals(self) -> dict[str, float]:
        with get_conn() as (_, cur):
            cur.execute("SELECT SUM(balance), SUM(total_spent) FROM users")
            bal, spent = cur.fetchone()  # type: ignore[misc]
        return {
            "total_balance": float(bal or 0),
            "total_spent": float(spent or 0),
        }

    def update_balance(self, user_id: int, new_balance: float) -> None:
        with get_conn() as (_, cur):
            cur.execute(
                "UPDATE users SET balance = %s WHERE id = %s",
                (new_balance, user_id),
            )
