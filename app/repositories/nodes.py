from typing import Any

from app.db import get_conn


class NodeRepository:
    """
    Very thin data-access layer around the *nodes* table.
    Returns the raw tuples you have been using in the templates.
    """

    def list(self) -> list[tuple[Any, ...]]:
        sql = "SELECT * FROM nodes"
        with get_conn() as (_, cur):
            cur.execute(sql)
            return cur.fetchall()

    def get(self, node_id: int) -> tuple[Any, ...] | None:
        with get_conn() as (_, cur):
            cur.execute("SELECT * FROM nodes WHERE id = %s", (node_id,))
            return cur.fetchone()

    def update(
        self,
        node_id: int,
        *,
        old_id: int | None,
        status: str | None,
        software: str | None,
        price: float | None,
        cpu: str | None,
        gpu: str | None,
        other_specs: str | None,
        licenses: str | None,
    ) -> None:
        sql = """
        UPDATE nodes
        SET old_id      = %s,
            status      = %s,
            software    = %s,
            price       = %s,
            cpu         = %s,
            gpu         = %s,
            other_specs = %s,
            licenses    = %s
        WHERE id = %s
        """
        with get_conn() as (_, cur):
            cur.execute(
                sql,
                (
                    old_id,
                    status,
                    software,
                    price,
                    cpu,
                    gpu,
                    other_specs,
                    licenses,
                    node_id,
                ),
            )

    def deactivate(self, node_id: int) -> None:
        with get_conn() as (_, cur):
            cur.execute(
                "UPDATE nodes SET status = 'unavailable' WHERE id = %s",
                (node_id,),
            )
