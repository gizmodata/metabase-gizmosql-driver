# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

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

[Unreleased]: https://github.com/gizmodata/metabase-gizmosql-driver/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/gizmodata/metabase-gizmosql-driver/releases/tag/v1.0.0
