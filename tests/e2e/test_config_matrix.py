"""Every connector option exercised with live connections."""
from conftest import GIZMO_DETAILS


def test_catalog_scopes_sync(mb, db_factory):
    db_id = db_factory("t-catalog", {**GIZMO_DETAILS, "catalog": "warehouse"})
    tables = mb.wait_synced_tables(db_id)
    schemas = {t["schema"] for t in tables}
    assert tables and schemas <= {"archive", "reports"}, schemas


def test_schema_filters_inclusion(mb, db_factory):
    db_id = db_factory("t-schema-filter", {**GIZMO_DETAILS,
                                           "schema-filters-type": "inclusion",
                                           "schema-filters-patterns": "sales"})
    tables = mb.wait_synced_tables(db_id)
    assert tables and {t["schema"] for t in tables} == {"sales"}


def test_connect_timeout_and_additional_options(mb, db_factory):
    db_id = db_factory("t-timeout-opts", {**GIZMO_DETAILS,
                                          "connect-timeout-millis": 5000,
                                          "additional-options": "threadPoolSize=2&retainAuth=true"})
    assert mb.native(db_id, "SELECT COUNT(*) FROM sales.orders").get("status") == "completed"


def test_use_token_off_ignores_stale_token(mb, db_factory):
    db_factory("t-toggle-precedence", {**GIZMO_DETAILS,
                                       "token-value": "stale-should-be-ignored"})
