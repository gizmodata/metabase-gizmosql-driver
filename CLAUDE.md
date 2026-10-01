# CLAUDE.md — Metabase GizmoSQL Driver

Clojure Metabase driver (`:gizmosql`, parent `:sql-jdbc`) for GizmoSQL —
GizmoData's DuckDB-backed Arrow Flight SQL server — over the GizmoSQL JDBC
driver (`com.gizmodata/gizmosql-jdbc-driver`). Forked from
J0hnG4lt/metabase-flightsql-driver at 0.4.0 and refocused on GizmoSQL.

## Skills (read these before working in their area)

- **[driver-dev](.claude/skills/driver-dev/SKILL.md)** — editing `src/` or the plugin manifest: build paths, rebuild cycle, pooling/connection-options invariants, auth-mode mapping, known failure signatures.
- **[metabase-api](.claude/skills/metabase-api/SKILL.md)** — scripting/validating Metabase via REST or MCP: API keys, field filters with aliases, dashboard parameters.

## Commands

- `/e2e-test` — full clean-slate end-to-end test (compose up → setup script → assertions).
- `/rebuild-driver` — rebuild the driver jar and restart Metabase after a code change.
- `/upgrade-metabase <ref>` — bump the Metabase pin (compose + CI matrix) with the driver-changelog checklist.

## Layout

```
src/metabase/driver/gizmosql.clj   # the whole driver
resources/metabase-plugin.yaml     # manifest: auth toggle, secrets, schema-filters
scripts/metabase_setup.py          # e2e: admin, API key -> .env, connection, dashboard
docker-compose.yaml                # metabase + postgres + gizmosql + maildev + builder
gizmosql/init.sql                  # 3 catalogs (memory/warehouse/staging), sales/hr/analytics
.github/workflows/build.yaml       # lint + matrix build {v0.62.19.5, v0.63.19.1} + driver-test-suite
.github/workflows/release.yaml     # vX.Y.Z tag -> gate (build.yaml + e2e.yml on the tag) -> GitHub Release
.github/workflows/e2e.yml          # full-stack pytest suite: weekly, on demand, and the release gate
```

## Build truth

Two build paths produce different artifacts — see the driver-dev skill. Compose uses the `builder` (lein) jar and **compile errors only appear in `podman compose logs metabase` at plugin load**; CI/releases use `bin/build-driver.sh` inside a Metabase checkout.

## Everyday commands

```bash
podman compose up -d                      # start everything
python scripts/metabase_setup.py          # setup + test dashboard; writes .env
podman compose logs metabase 2>&1 | tail -100
podman compose logs metabase 2>&1 | grep -i "hash.*changed\|connections:"   # pool health
```

Metabase: http://localhost:3000 (admin@metabase.local / Metabase123!)

## Releases

Keep-a-Changelog + semver tags (no release-please). Flow: move `[Unreleased]`
into a `## [X.Y.Z] - YYYY-MM-DD` section, bump `version.txt` + `project.clj`,
commit, `git push origin main vX.Y.Z`. release.yaml first runs build.yaml
(lint, per-Metabase jars, driver-test-suite) and e2e.yml on the tagged commit
as reusable workflows; only if both pass does it verify version.txt matches
the tag and publish the GitHub Release with those tested jars and the
CHANGELOG section as notes. A red e2e blocks the release — fix it, don't bypass.

## MCP

`.mcp.json` runs a Metabase MCP server (`@imlewc/metabase-server`) against the local stack — export `METABASE_API_KEY` from `.env` first. The bundled official MCP server (`/api/metabase-mcp`, OAuth) suits interactive exploration only.

## Non-negotiables

1. `connection-details->spec` must be hash-stable (pool invalidation otherwise) — named fns only.
2. Secret-typed properties resolve via `driver-api/secret-value-as-string` — never `(:token details)` alone.
3. No `DatabaseMetaData` transaction/isolation probes (NPE on incomplete `GetSqlInfo` servers).
4. Before bumping Metabase: read `docs/developers-guide/driver-changelog.md` at the target ref; unknown feature keywords throw at load.
5. Verify changes with `/e2e-test` — compilation alone proves nothing on the compose path.
