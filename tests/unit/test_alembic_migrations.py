from pathlib import Path

from alembic.config import Config


SERVICE_MIGRATION_TABLES = {
    "auth_service": {
        "users",
        "user_profiles",
        "user_addresses",
        "roles",
        "user_roles",
    },
    "product_service": {"categories", "products"},
    "order_service": {"orders", "order_items", "outbox_events", "inbox_events"},
    "payment_service": {"payments", "outbox_events", "inbox_events"},
}


def test_service_alembic_configs_point_to_local_migration_trees() -> None:
    for service_name in SERVICE_MIGRATION_TABLES:
        config_path = Path("apps") / service_name / "alembic.ini"
        config = Config(str(config_path))

        assert config_path.exists()
        assert config.get_main_option("script_location").endswith(
            f"apps/{service_name}/migrations"
        )


def test_initial_migrations_create_expected_service_tables() -> None:
    for service_name, table_names in SERVICE_MIGRATION_TABLES.items():
        versions_path = Path("apps") / service_name / "migrations" / "versions"
        migration_text = "\n".join(path.read_text() for path in versions_path.glob("*.py"))

        for table_name in table_names:
            assert f'"{table_name}"' in migration_text
