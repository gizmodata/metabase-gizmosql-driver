# Introduction to metabase-gizmosql-driver

A Metabase driver for [GizmoSQL](https://gizmosql.com), GizmoData's
[Arrow Flight SQL](https://arrow.apache.org/docs/format/FlightSql.html)
server backed by DuckDB. The bundled compose stack demonstrates it end to end.

## Quick start

```bash
podman-compose up -d              # pip install podman-compose on Windows (see README troubleshooting)
python scripts/metabase_setup.py  # admin user, API key -> .env, connection, demo dashboards
```

Metabase: http://localhost:3000 (`admin@metabase.local` / `Metabase123!`).

> **Metabase 63+ note:** the official image runs JDK 25, which needs extra JVM flags for Arrow — the compose file sets them. See *"Java / JVM requirements"* in the main README before deploying anywhere else.

## The demo server

The compose stack's `gizmosql` service (username/password auth, port 31337)
seeds 3 catalogs (`memory`/`warehouse`/`staging`) with multi-schema test data
(`sales`/`hr`/`analytics`), and supports **writes: CSV uploads + Data Studio
transforms** plus JWT roles via the OAuth profile.

## Connection recipes

**Authentication** is a toggle: *off* = username/password (use the literal username `token` for GizmoSQL external JWTs), *on* = bearer token. Everything credential-like is stored as a Metabase secret.

- **Catalog** scopes sync to one catalog (e.g. `warehouse`).
- **Schemas** (include/exclude patterns) filter what syncs.
- **Advanced**: CA certificate / mTLS client cert+key (PEM secrets), connect timeout, *Writable backend* toggle (enables CSV uploads and Data Studio table transforms), and **Additional options** — the escape hatch for anything the GizmoSQL JDBC driver understands (`threadPoolSize`, `retainAuth`, `oauth.*`) plus unknown params which are forwarded as gRPC headers.

## Optional profiles

```bash
# TLS/mTLS (gizmosql-tls :31338 CA-signed, gizmosql-mtls :31339 requires client certs)
./scripts/generate_tls_certs.sh
podman-compose -f docker-compose.yaml -f docker-compose.tls.yaml up -d

# OAuth2 (Keycloak realm minting role-scoped JWTs; gizmosql-oauth :31340 verifies them)
python scripts/generate_oauth_config.py
podman-compose -f docker-compose.yaml -f docker-compose.oauth.yaml up -d keycloak gizmosql-oauth
```

## Testing

```bash
python -m pytest tests/e2e -v     # API-level tests; optional stacks auto-skip
```

CI additionally runs Metabase's own shared driver test harness (Clojure test extensions under `test/`) against a GizmoSQL service. See `tests/e2e/README.md`.

## Walkthrough screenshots

> Taken on an earlier Metabase/driver version — the connection form now shows the auth toggle and TLS fields, but the flow is unchanged.

Add the connection, then sync and explore:

![connection](/docs/connection.png)
![database-sync](/docs/database-sync.png)
![sql-editor](/docs/sql-editor.png)
![browse-data](/docs/browse-data.png)
![visual-editor](/docs/visual-editor.png)
