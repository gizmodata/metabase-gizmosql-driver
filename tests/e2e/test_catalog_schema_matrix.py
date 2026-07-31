"""Catalog + multi-schema + schema-filters behavior against GizmoSQL.

GizmoSQL/DuckDB catalog/schema topology:
  catalogs memory (sales/hr/analytics + main), warehouse (archive/reports),
  staging (imports)

Tests live-discover information_schema first so they document actual
semantics rather than assumptions.
"""
from conftest import GIZMO_DETAILS


def schemas_of(tables):
    return {t["schema"] for t in tables}


def test_gizmo_staging_catalog_scopes_sync(mb, db_factory):
    db_id = db_factory("cs-gizmo-staging", {**GIZMO_DETAILS, "catalog": "staging"})
    tables = mb.wait_synced_tables(db_id)
    # DuckDB attaches a per-catalog temp schema alongside the data schema
    assert tables and "imports" in schemas_of(tables) \
        and schemas_of(tables) <= {"imports", "temp"}, schemas_of(tables)


def test_gizmo_nonexistent_catalog_syncs_nothing(mb, db_factory):
    db_id = db_factory("cs-gizmo-nocat", {**GIZMO_DETAILS, "catalog": "does_not_exist"})
    tables = mb.wait_synced_tables(db_id, timeout_s=45)
    assert tables == [], [t["name"] for t in tables]


def test_gizmo_catalog_plus_schema_filter_compose(mb, db_factory):
    """catalog=memory AND inclusion filter hr -> only hr schema tables."""
    db_id = db_factory("cs-gizmo-cat-plus-filter",
                       {**GIZMO_DETAILS, "catalog": "memory",
                        "schema-filters-type": "inclusion",
                        "schema-filters-patterns": "hr"})
    tables = mb.wait_synced_tables(db_id)
    assert tables and schemas_of(tables) == {"hr"}, schemas_of(tables)


def test_gizmo_exclusion_filter(mb, db_factory):
    db_id = db_factory("cs-gizmo-exclude",
                       {**GIZMO_DETAILS, "catalog": "memory",
                        "schema-filters-type": "exclusion",
                        "schema-filters-patterns": "hr,analytics,main"})
    tables = mb.wait_synced_tables(db_id)
    assert tables and schemas_of(tables) == {"sales"}, schemas_of(tables)
