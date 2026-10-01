"""Core smoke: connections, dashboard shape, native queries, token storage shapes."""


def test_demo_connection_exists(mb):
    dbs = mb.databases()
    assert "gizmo" in dbs


def test_dashboard_shape(mb):
    _, dashboards = mb.get("/api/dashboard")
    rows = dashboards["data"] if isinstance(dashboards, dict) and "data" in dashboards else dashboards
    target = next((d for d in rows if "GizmoSQL" in (d.get("name") or "")), None)
    assert target, "test dashboard missing — run scripts/metabase_setup.py"
    _, dash = mb.get(f"/api/dashboard/{target['id']}")
    assert len(dash["dashcards"]) == 32
    assert len(dash["parameters"]) == 5


def test_native_query_gizmosql(mb):
    dbs = mb.databases()
    res = mb.native(dbs["gizmo"]["id"], "SELECT COUNT(*) FROM sales.orders")
    assert res.get("status") == "completed" and res["data"]["rows"][0][0] > 0


def test_filtered_query_via_dashboard_parameter(mb):
    _, dash = mb.get("/api/dashboard/2")
    card_id = next(dc["card_id"] for dc in dash["dashcards"]
                   for pm in dc.get("parameter_mappings") or []
                   if pm.get("parameter_id") == "status")
    _, res = mb.post(f"/api/card/{card_id}/query", {
        "parameters": [{"id": "status", "type": "string/=", "value": ["Delivered"],
                        "target": ["dimension", ["template-tag", "status"]]}]})
    assert res.get("status") == "completed" and len(res["data"]["rows"]) > 0
