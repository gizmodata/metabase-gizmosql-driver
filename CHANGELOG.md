# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1] - 2026-10-01

### Fixed

- Releases are now gated on the full test suite: `release.yaml` runs
  `build.yaml` (lint, per-Metabase builds, driver-test-suite) and the e2e
  stack (`e2e.yml`) on the tagged commit and publishes only if both pass,
  attaching the jars that gate built. Previously no tests ran before a release,
  and the weekly e2e run had been failing since August unnoticed.
- e2e OAuth role tests: the admin write check always failed because Metabase's
  native-query API reports any statement without a result set (DDL, plain
  DML) as failed even though it ran, and the readonly check passed trivially
  for the same reason. Both now use `INSERT ... RETURNING` and assert on
  GizmoSQL's readonly-session rejection message.
- e2e suite adapted to Metabase 0.63.19 API changes (card query parameters
  need an `id`, segment definitions must be full queries, segments are
  archived via `PUT`, cache writes land after the response) and MailDev 3's
  `/api/email` endpoint.
- The compose builder's jar now has a fixed name
  (`gizmosql.metabase-driver-standalone.jar` via `:uberjar-name`). The compose
  file hardcoded `…-1.0.0-SNAPSHOT-standalone.jar`, so bumping `project.clj`
  left Metabase waiting for a jar that never appeared. The first gated v1.0.1
  release run failed on exactly this and published nothing.
- e2e gate hardening: the health wait uses `curl --max-time` with a step
  timeout and dumps builder logs on failure. In CI (`E2E_STRICT=1`) a skipped
  test counts as a failure, so a profile container that never started can't
  pass the gate with partial coverage.

### Changed

- Dependency bumps: Metabase build/test targets v0.62.19.5 and v0.63.19.1
  (compose image v0.63.19.1), GizmoSQL v1.40.0, Clojure 1.12.3 (matches
  Metabase), Keycloak 26.8, Postgres 17.10, MailDev 3.0.0; CI actions
  setup-java v6, setup-clojure 13.7.0, Clojure CLI 1.12.6.1673,
  clj-kondo 2026.08.04.
- Compose services no longer set a fixed `container_name`, so the dev stack
  can coexist with other GizmoSQL containers on the same machine; docs and
  commands now use compose-scoped `podman compose logs/exec <service>`.

## [1.0.0] - 2026-07-31

First GizmoData release. This project began as a fork of
[J0hnG4lt/metabase-flightsql-driver](https://github.com/J0hnG4lt/metabase-flightsql-driver)
(Apache-2.0) at its 0.4.0 release, refocused from a generic Arrow Flight SQL
driver into a dedicated GizmoSQL driver.

### Added

- Tag-triggered release workflow: pushing a `vX.Y.Z` tag builds the driver
  against every supported Metabase line and publishes a GitHub Release with
  the jars attached and the matching CHANGELOG section as release notes.

### Changed

- Driver renamed `:arrow-flight-sql` → `:gizmosql`; display name is now
  **GizmoSQL** and the Metabase engine key is `gizmosql`.
- Swapped the Apache Arrow Flight SQL JDBC driver for GizmoData's
  `com.gizmodata/gizmosql-jdbc-driver` 1.7.0 (`jdbc:gizmosql://` URLs,
  timestamp-TZ fixes, richer metadata via `_gizmosql_system`).
- Default port is now 31337 (GizmoSQL's default) instead of 443.
- CHANGELOG switched to Keep-a-Changelog format; release-please removed.

### Removed

- Non-GizmoSQL test backends and their profiles: Spice.ai, InfluxDB 3,
  quack-on-demand, Apache Doris, StarRocks, and Dremio. The compose stack and
  e2e suite now target GizmoSQL only (base, TLS/mTLS, and OAuth profiles).

[Unreleased]: https://github.com/gizmodata/metabase-gizmosql-driver/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/gizmodata/metabase-gizmosql-driver/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/gizmodata/metabase-gizmosql-driver/releases/tag/v1.0.0
