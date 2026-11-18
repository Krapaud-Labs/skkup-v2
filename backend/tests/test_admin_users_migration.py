"""SQLite schema checks for the Admin audit migration."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

MIGRATION = Path(__file__).parents[1] / "migrations" / "versions" / "0004_admin_user_audit.py"
EDITORIAL_MIGRATION = (
    Path(__file__).parents[1] / "migrations" / "versions" / "0005_admin_editorial.py"
)
SPONSOR_MIGRATION = Path(__file__).parents[1] / "migrations" / "versions" / "0006_admin_sponsors.py"
AUDIT_TIMELINE_MIGRATION = (
    Path(__file__).parents[1] / "migrations" / "versions" / "0007_admin_audit_timeline.py"
)
FRAUD_FLAGS_MIGRATION = (
    Path(__file__).parents[1] / "migrations" / "versions" / "0008_admin_fraud_flags.py"
)
RAFFLE_CONFIGURATION_MIGRATION = (
    Path(__file__).parents[1] / "migrations" / "versions" / "0009_admin_raffle_configuration.py"
)


class AdminUsersMigrationTests(unittest.TestCase):
    def test_upgrade_creates_audit_indexes_and_downgrade_removes_them(self) -> None:
        spec = importlib.util.spec_from_file_location("migration_0004_admin_user_audit", MIGRATION)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("CREATE TABLE users (id VARCHAR(36) PRIMARY KEY)")
                with Operations.context(MigrationContext.configure(connection)):
                    migration.upgrade()
                inspector = inspect(connection)
                self.assertIn("admin_audit_events", inspector.get_table_names())
                self.assertEqual(
                    {index["name"] for index in inspector.get_indexes("admin_audit_events")},
                    {"ix_admin_audit_target_created", "ix_admin_audit_actor_created"},
                )
                with Operations.context(MigrationContext.configure(connection)):
                    migration.downgrade()
                self.assertNotIn("admin_audit_events", inspect(connection).get_table_names())
        finally:
            engine.dispose()

    def test_editorial_migration_creates_and_drops_tables_in_fk_order(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "migration_0005_admin_editorial", EDITORIAL_MIGRATION
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("CREATE TABLE users (id VARCHAR(36) PRIMARY KEY)")
                with Operations.context(MigrationContext.configure(connection)):
                    migration.upgrade()
                inspector = inspect(connection)
                self.assertTrue(
                    {"announcements", "managed_contents", "content_versions"}.issubset(
                        inspector.get_table_names()
                    )
                )
                self.assertEqual(
                    {index["name"] for index in inspector.get_indexes("managed_contents")},
                    {"ix_managed_contents_type_locale_status"},
                )
                with Operations.context(MigrationContext.configure(connection)):
                    migration.downgrade()
                tables = inspect(connection).get_table_names()
                self.assertFalse(
                    {"announcements", "managed_contents", "content_versions"}.intersection(tables)
                )
        finally:
            engine.dispose()

    def test_sponsor_migration_creates_and_drops_catalogue(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "migration_0006_admin_sponsors", SPONSOR_MIGRATION
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                with Operations.context(MigrationContext.configure(connection)):
                    migration.upgrade()
                inspector = inspect(connection)
                self.assertIn("sponsors", inspector.get_table_names())
                self.assertEqual(
                    {column["name"] for column in inspector.get_columns("sponsors")},
                    {"id", "nom", "logo_url", "actif", "created_at"},
                )
                self.assertEqual(
                    {index["name"] for index in inspector.get_indexes("sponsors")},
                    {"ix_sponsors_active"},
                )
                with Operations.context(MigrationContext.configure(connection)):
                    migration.downgrade()
                self.assertNotIn("sponsors", inspect(connection).get_table_names())
        finally:
            engine.dispose()

    def test_audit_timeline_migration_adds_and_removes_order_index(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "migration_0007_admin_audit_timeline", AUDIT_TIMELINE_MIGRATION
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql(
                    "CREATE TABLE admin_audit_events "
                    "(id VARCHAR(36) PRIMARY KEY, created_at DATETIME NOT NULL)"
                )
                with Operations.context(MigrationContext.configure(connection)):
                    migration.upgrade()
                self.assertIn(
                    "ix_admin_audit_created",
                    {
                        index["name"]
                        for index in inspect(connection).get_indexes("admin_audit_events")
                    },
                )
                with Operations.context(MigrationContext.configure(connection)):
                    migration.downgrade()
                self.assertNotIn(
                    "ix_admin_audit_created",
                    {
                        index["name"]
                        for index in inspect(connection).get_indexes("admin_audit_events")
                    },
                )
        finally:
            engine.dispose()

    def test_fraud_flag_migration_has_no_watch_session_dependency(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "migration_0008_admin_fraud_flags", FRAUD_FLAGS_MIGRATION
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("CREATE TABLE users (id VARCHAR(36) PRIMARY KEY)")
                with Operations.context(MigrationContext.configure(connection)):
                    migration.upgrade()
                inspector = inspect(connection)
                self.assertIn("fraud_flags", inspector.get_table_names())
                self.assertEqual(
                    {column["name"] for column in inspector.get_columns("fraud_flags")},
                    {"id", "user_id", "type", "details", "statut", "created_at", "examinee_at"},
                )
                foreign_keys = inspector.get_foreign_keys("fraud_flags")
                self.assertEqual(len(foreign_keys), 1)
                self.assertEqual(foreign_keys[0]["referred_table"], "users")
                self.assertEqual(
                    {index["name"] for index in inspector.get_indexes("fraud_flags")},
                    {"ix_fraud_flags_user_status", "ix_fraud_flags_created"},
                )
                with Operations.context(MigrationContext.configure(connection)):
                    migration.downgrade()
                self.assertNotIn("fraud_flags", inspect(connection).get_table_names())
        finally:
            engine.dispose()

    def test_raffle_configuration_migration_excludes_draw_result_fields(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "migration_0009_admin_raffle_configuration", RAFFLE_CONFIGURATION_MIGRATION
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("CREATE TABLE sponsors (id VARCHAR(36) PRIMARY KEY)")
                with Operations.context(MigrationContext.configure(connection)):
                    migration.upgrade()
                inspector = inspect(connection)
                raffle_columns = {column["name"] for column in inspector.get_columns("raffles")}
                self.assertEqual(
                    raffle_columns,
                    {
                        "id",
                        "titre",
                        "description",
                        "date_ouverture",
                        "date_tirage",
                        "statut",
                        "engagement_graine",
                    },
                )
                self.assertEqual(
                    {column["name"] for column in inspector.get_columns("raffle_lots")},
                    {
                        "id",
                        "raffle_id",
                        "sponsor_id",
                        "nom",
                        "valeur_estimee",
                        "quantite",
                        "fournisseur",
                        "image_url",
                    },
                )
                self.assertEqual(
                    {index["name"] for index in inspector.get_indexes("raffle_lots")},
                    {"ix_raffle_lots_raffle", "ix_raffle_lots_sponsor"},
                )
                with Operations.context(MigrationContext.configure(connection)):
                    migration.downgrade()
                tables = inspect(connection).get_table_names()
                self.assertNotIn("raffle_lots", tables)
                self.assertNotIn("raffles", tables)
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
