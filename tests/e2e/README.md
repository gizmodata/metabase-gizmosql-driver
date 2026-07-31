# Driver e2e suite

API-level end-to-end tests against the compose stack (metabase + postgres +
gizmosql + maildev). Stdlib + pytest only.

```bash
# 1. Base stack + setup (writes METABASE_API_KEY to .env)
docker compose up -d          # (or podman-compose; see main README)
python scripts/metabase_setup.py

# 2. Optional: TLS/mTLS profile (gizmosql-tls on host port 31338)
./scripts/generate_tls_certs.sh
docker compose -f docker-compose.yaml -f docker-compose.tls.yaml up -d

# 3. Optional: OAuth profile (Keycloak-backed GizmoSQL)
docker compose -f docker-compose.yaml -f docker-compose.oauth.yaml up -d

# 4. Run
python -m pytest tests/e2e -v
```

| Module | Covers |
|---|---|
| `test_core.py` | connection, dashboard shape, native query, dashboard-parameter filtered query |
| `test_config_matrix.py` | catalog scoping, schema-filters, connect timeout, additional-options, toggle precedence |
| `test_auth_manifest.py` | manifest field expansion (types, visible-if, advanced gating), normalize-db-details backfill |
| `test_features.py` | every dashboard card (11 visual types), sync_schema/rescan_values, MBQL temporal breakout + relative filters, segments, v2 metrics, pivot |
| `test_tls.py` | TLS skip-verify, CA validation via tlsRootCerts, mTLS client certs, strict-mode negatives (auto-skips without the TLS profile) |
| `test_operations.py` | query caching (cached flag on repeat run), x-ray dashboard generation, rows-alert email delivery via maildev (auto-skips without maildev) |
| `test_uploads.py` | CSV upload → typed table + model → query → append-csv round trip on GizmoSQL; per-connection feature gating |
| `test_transforms.py` | Data Studio `:transforms/table` — CTAS transform runs and creates the output table on GizmoSQL |
| `test_catalog_schema_matrix.py` | catalog scoping + include/exclude schema filters across GizmoSQL's 3 catalogs (memory/warehouse/staging) |
| `test_oauth.py` | Keycloak-minted JWTs: admin role read/write, readonly role SELECT-only, tampered-token rejection, and a pinned test documenting that GizmoSQL Core rejects header-borne external bearers from the JDBC `oauth.*` flow (auto-skips without the OAuth profile) |

There is also a Clojure test layer under the repo-root `test/` directory: pure unit tests for the connection spec builder plus Metabase's shared driver harness (test extensions) — run by the `driver-test-suite` CI job, or locally from a Metabase checkout with `DRIVERS=gizmosql clojure -X:dev:drivers:drivers-dev:test :only '[metabase.driver.gizmosql-test]'`.
