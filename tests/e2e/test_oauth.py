"""OAuth2 profile (docker-compose.oauth.yaml): Keycloak-minted JWTs against
GizmoSQL with signature/issuer/audience verification and role enforcement.

Key finding encoded below: GizmoSQL Core accepts EXTERNAL JWTs only via the
Flight handshake (username literally "token", JWT as password). The JDBC
``oauth.*`` client_credentials flow does fetch and send the Keycloak token as
a bearer header (verified in server logs), but Core's bearer-header path only
accepts its own session tokens — header-borne external JWTs are an
Enterprise (JWKS) capability. Use Username="token" + the OAuth token as
Password with this server.
"""
import json
import urllib.parse
import urllib.request

import pytest

from conftest import REPO_ROOT, port_open

requires_oauth_stack = pytest.mark.skipif(
    not (REPO_ROOT / "oauth" / "signing-cert.pem").exists()
    or not port_open("localhost", 8180)
    or not port_open("localhost", 31340),
    reason="OAuth profile not running (scripts/generate_oauth_config.py + docker-compose.oauth.yaml)")

pytestmark = requires_oauth_stack

KC_TOKEN_URL = "http://localhost:8180/realms/gizmosql/protocol/openid-connect/token"
IN_NETWORK_TOKEN_URL = "http://keycloak:8080/realms/gizmosql/protocol/openid-connect/token"

GIZMO_OAUTH = {"host": "gizmosql-oauth", "port": 31337, "use-token": False,
               "useEncryption": False, "disableCertificateVerification": True}


def keycloak_token(client_id, secret):
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": secret}).encode()
    with urllib.request.urlopen(KC_TOKEN_URL, data, timeout=30) as r:
        return json.load(r)["access_token"]


def jwt_details(jwt):
    return {**GIZMO_OAUTH, "username": "token", "password": jwt}


# Metabase's native-query API executes a statement and then fails it with
# "Select statement did not produce a ResultSet" when it returns no rows-set,
# even though the statement ran. So DDL/plain DML is never "completed" there;
# role checks use INSERT ... RETURNING (a write that yields a result set) and
# assert on GizmoSQL's own readonly-session rejection text.
NO_RESULT_SET = "did not produce a ResultSet"
READONLY_REJECTION = "has a readonly session and cannot run statements that modify state"


def test_keycloak_jwt_admin_connects_and_writes(mb, db_factory):
    jwt = keycloak_token(client_id="gizmosql-m2m", secret="m2m-demo-secret-0123456789")
    db_id = db_factory("t-kc-admin", jwt_details(jwt=jwt))
    res = mb.native(db_id, "SELECT COUNT(*) FROM sales.orders")
    assert res.get("status") == "completed" and res["data"]["rows"][0][0] > 0
    res = mb.native(db_id, "CREATE OR REPLACE TABLE main.oauth_admin_probe(id INT)")
    assert NO_RESULT_SET in (res.get("error") or ""), res.get("error")
    try:
        res = mb.native(db_id, "INSERT INTO main.oauth_admin_probe VALUES (42) RETURNING id")
        assert res.get("status") == "completed", res.get("error")
        assert res["data"]["rows"] == [[42]]
    finally:
        mb.native(db_id, "DROP TABLE IF EXISTS main.oauth_admin_probe")


def test_keycloak_jwt_readonly_role_is_select_only(mb, db_factory):
    jwt = keycloak_token(client_id="gizmosql-readonly", secret="readonly-demo-secret-0123456789")
    db_id = db_factory("t-kc-readonly", jwt_details(jwt=jwt))
    res = mb.native(db_id, "SELECT COUNT(*) FROM sales.customers")
    assert res.get("status") == "completed" and res["data"]["rows"][0][0] > 0
    for sql in ("CREATE TABLE main.readonly_probe(id INT)",
                "INSERT INTO sales.customers SELECT * FROM sales.customers WHERE false"
                " RETURNING customer_id"):
        res = mb.native(db_id, sql)
        assert res.get("status") == "failed", f"readonly role unexpectedly ran: {sql}"
        assert READONLY_REJECTION in (res.get("error") or ""), res.get("error")


def test_tampered_jwt_rejected(mb, db_factory):
    jwt = keycloak_token("gizmosql-m2m", "m2m-demo-secret-0123456789")
    bad = jwt[:-20] + "A" * 20
    db_id = db_factory("t-kc-tampered", jwt_details(bad), expect_ok=False)
    assert db_id is None


def test_jdbc_oauth_bearer_header_not_accepted_by_core(mb, db_factory):
    """Pins the known GizmoSQL Core limitation (see module docstring): the
    JDBC oauth.* flow sends the token as a bearer HEADER, which Core's
    session-token validator rejects (reason=invalid_issuer in server logs)
    even though issuer/audience/signature config matches. If this test ever
    FAILS (i.e. the connection succeeds), Core gained external-bearer
    support — update the docs and promote this to a positive test."""
    opts = ("oauth.flow=client_credentials"
            f"&oauth.tokenUri={IN_NETWORK_TOKEN_URL}"
            "&oauth.clientId=gizmosql-m2m"
            "&oauth.clientSecret=m2m-demo-secret-0123456789")
    db_id = db_factory("t-kc-oauth-header", {**GIZMO_OAUTH, "additional-options": opts},
                       expect_ok=False)
    assert db_id is None
