from app.db import get_conn

class UserRepository:
    def find_many(self, *, search: str = "", sort_by: str = "id", order: str = "asc"):
        sort_by  = sort_by if sort_by in {"id","telegram_id","balance","total_spent"} else "id"
        order_sql = "ASC" if order == "asc" else "DESC"

        sql = f"""
            SELECT id, telegram_id, total_spent, balance,
                   first_name, last_name, username, language_code
            FROM   users
            WHERE  (%s = '' OR username ILIKE %(like)s
                              OR first_name ILIKE %(like)s
                              OR last_name  ILIKE %(like)s
                              OR language_code ILIKE %(like)s)
            ORDER  BY {sort_by} {order_sql}
        """
        with get_conn() as (_, cur):
            cur.execute(sql, {"": "", "like": f"%{search}%"})
            return cur.fetchall()

    def totals(self):
        with get_conn() as (_, cur):
            cur.execute("SELECT SUM(balance), SUM(total_spent) FROM users")
            bal, spent = cur.fetchone()
            return {"total_balance": float(bal or 0), "total_spent": float(spent or 0)}

    def update_balance(self, user_id: int, new_balance: float) -> None:
        with get_conn() as (_, cur):
            cur.execute(
                "UPDATE users SET balance = %s WHERE id = %s",
                (new_balance, user_id),
            )
