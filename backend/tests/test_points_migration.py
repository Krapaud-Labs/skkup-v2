"""SQLite compatibility checks for the issue #6 Alembic DDL."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

MIGRATION = Path(__file__).parents[1] / "migrations" / "versions" / "0003_viewer_points.py"


class ViewerPointsMigrationTests(unittest.TestCase):
    def test_migration_creates_tables_and_database_idempotency_constraints(self) -> None:
        spec = importlib.util.spec_from_file_location("migration_0003_viewer_points", MIGRATION)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("CREATE TABLE users (id VARCHAR(36) PRIMARY KEY)")
                connection.execute(text("INSERT INTO users (id) VALUES ('viewer-1')"))
                with Operations.context(MigrationContext.configure(connection)):
                    migration.upgrade()

                present = set(inspect(connection).get_table_names())
                self.assertTrue(
                    {
                        "points_transactions",
                        "daily_checkins",
                        "scratch_card_grants",
                        "reward_tickets",
                    }.issubset(present)
                )
                connection.execute(
                    text(
                        "INSERT INTO daily_checkins "
                        "(id,user_id,local_day,streak_after,max_streak_after,"
                        "points_balance_after,scratch_card_due) "
                        "VALUES ('checkin-1','viewer-1','2030-01-01',1,1,0,0)"
                    )
                )
                with self.assertRaises(IntegrityError), connection.begin_nested():
                    connection.execute(
                        text(
                            "INSERT INTO daily_checkins "
                            "(id,user_id,local_day,streak_after,max_streak_after,"
                            "points_balance_after,scratch_card_due) "
                            "VALUES ('checkin-2','viewer-1','2030-01-01',1,1,0,0)"
                        )
                    )
                connection.execute(
                    text(
                        "INSERT INTO points_transactions "
                        "(id,user_id,amount,balance_after,type,idempotency_key) "
                        "VALUES ('point-1','viewer-1',0,0,'CARTE_A_GRATTER','scratch:none')"
                    )
                )
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
