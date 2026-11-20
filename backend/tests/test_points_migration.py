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
RAFFLE_MIGRATION = (
    Path(__file__).parents[1] / "migrations" / "versions" / "0009_admin_raffle_configuration.py"
)
ISSUE9_MIGRATION = (
    Path(__file__).parents[1] / "migrations" / "versions" / "0010_scratch_and_raffle_draws.py"
)


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

    def test_issue9_migration_adds_scratch_states_and_distinct_raffle_entries(self) -> None:
        migrations = []
        for module_name, path in (
            ("migration_0003_viewer_points", MIGRATION),
            ("migration_0009_raffles", RAFFLE_MIGRATION),
            ("migration_0010_issue9", ISSUE9_MIGRATION),
        ):
            spec = importlib.util.spec_from_file_location(module_name, path)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            migrations.append(module)

        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("CREATE TABLE users (id VARCHAR(36) PRIMARY KEY)")
                connection.exec_driver_sql("CREATE TABLE sponsors (id VARCHAR(36) PRIMARY KEY)")
                for migration in migrations[:1]:
                    with Operations.context(MigrationContext.configure(connection)):
                        migration.upgrade()
                with Operations.context(MigrationContext.configure(connection)):
                    migrations[1].upgrade()
                with Operations.context(MigrationContext.configure(connection)):
                    migrations[2].upgrade()
                tables = set(inspect(connection).get_table_names())
                self.assertTrue(
                    {"raffle_tickets", "raffle_winners", "raffle_draw_audits"}.issubset(tables)
                )
                self.assertIn(
                    "outcome_type",
                    {
                        column["name"]
                        for column in inspect(connection).get_columns("reward_tickets")
                    },
                )
                self.assertIn(
                    "uq_raffle_ticket_user_raffle",
                    {
                        constraint["name"]
                        for constraint in inspect(connection).get_unique_constraints(
                            "raffle_tickets"
                        )
                    },
                )
                with Operations.context(MigrationContext.configure(connection)):
                    migrations[2].downgrade()
                self.assertNotIn("raffle_tickets", inspect(connection).get_table_names())
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
