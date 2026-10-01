# Metabase GizmoSQL Driver

A Metabase driver for [GizmoSQL](https://gizmosql.com) — GizmoData's Arrow
Flight SQL server backed by DuckDB. Connects via the
[GizmoSQL JDBC driver](https://github.com/gizmodata/gizmosql-jdbc-driver)
(`com.gizmodata/gizmosql-jdbc-driver`), GizmoData's enhanced build of the
Apache Arrow Flight SQL JDBC driver.

Forked from
[J0hnG4lt/metabase-flightsql-driver](https://github.com/J0hnG4lt/metabase-flightsql-driver)
(Apache-2.0) and refocused on GizmoSQL.

## Features

- Registers as the **GizmoSQL** database type (`gizmosql`, parent `sql-jdbc`).
- Username/password (Flight handshake), bearer-token/JWT, and OAuth2 auth.
- TLS by default, with custom CA and mTLS client-certificate support.
- Catalog selection plus schema include/exclude filters during sync.
- Field filters, MBQL, native SQL, pivot tables, and dashboard parameters.
- CSV uploads and Data Studio table transforms (opt-in per connection).
- Timestamp/date/time conversion tuned for GizmoSQL's DuckDB backend.

## Compatibility

CI builds one jar per supported Metabase release line (see release assets):

| Driver release | Metabase | GizmoSQL JDBC | Notes |
|---|---|---|---|
| 1.0.1 | v0.62.19.5 (`-mb62` jar), v0.63.19.1 (`-mb63` jar) | 1.7.0 | Metabase 62.x reached EOL 2026-09-01 |
| 1.0.0 | v0.62.5 (`-mb62` jar), v0.63.1 (`-mb63` jar) | 1.7.0 | MB 63 image runs JDK 25 — see *Java / JVM requirements* |

## Java / JVM requirements (important for Metabase 63+)

The official **Metabase v0.63 Docker image runs JDK 25** (v0.62 ran JDK 21).
Two JDK-25 changes break the Arrow-based memory allocator at first connection
with:

```
Could not initialize class ...arrow.memory.RootAllocator
```

1. **JEP 498**: `sun.misc.Unsafe` memory-access methods are disabled by
   default on JDK 24+ — Arrow's allocator depends on them.
2. The image's default flags no longer open `java.nio` internals to unnamed
   modules.

**Fix — pass these JVM options to Metabase** (the bundled
`docker-compose.yaml` already does):

```yaml
environment:
  JAVA_OPTS: >-
    --add-opens=java.base/java.nio=ALL-UNNAMED
    --add-opens=java.base/sun.nio.ch=ALL-UNNAMED
    --sun-misc-unsafe-memory-access=allow
    --enable-native-access=ALL-UNNAMED
    -Dio.netty.tryReflectionSetAccessible=true
```

For bare-JVM installs, add the same flags to the `java ... -jar metabase.jar`
command line. On Metabase ≤ 62 (JDK 21) only the two `--add-opens` are needed
and the image already includes them; `--sun-misc-unsafe-memory-access` is
unknown to JDK ≤ 22 and must be omitted there.

> Symptom guide: the driver *loads* and registers fine at startup — the
> failure appears only on the first real connection/health-check, and once the
> class-init fails the JVM caches the failure until restart.

## Installation

Download the jar matching your Metabase line from the
[latest release](https://github.com/gizmodata/metabase-gizmosql-driver/releases/latest)
(`gizmosql.metabase-driver-mb62.jar` or `-mb63.jar`), drop it into Metabase's
`plugins/` directory, add the JVM flags above, and restart Metabase. Then add
a database of type **GizmoSQL** in **Admin → Databases**.

## Local development

### Prerequisites

- Podman or Docker – for the compose stack.
- Python 3 – for the automated setup script.
- Leiningen – optional, for local builds (the compose `builder` service
  handles this automatically).

### Quick Start

1. Clone the repository

   ```bash
   git clone https://github.com/gizmodata/metabase-gizmosql-driver.git
   cd metabase-gizmosql-driver
   ```

2. Start all services

   ```bash
   podman compose up -d
   ```

3. Wait for Metabase to be ready (takes ~1-2 minutes for the jar build +
   Metabase startup)

   ```bash
   podman compose exec metabase curl -s http://localhost:3000/api/health
   ```

4. Run the automated setup script

   ```bash
   python scripts/metabase_setup.py
   ```

   This script performs initial Metabase setup (admin user + API key),
   creates the GizmoSQL connection, and builds a comprehensive test
   dashboard with field filters.

5. Open Metabase at http://localhost:3000
   - Email: `admin@metabase.local`
   - Password: `Metabase123!`

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| metabase | 3000 | Metabase BI tool |
| postgres | 5432 | Metabase application database |
| gizmosql | 31337 | GizmoSQL server (DuckDB-backed, demo credentials) |
| maildev | 1080, 1025 | SMTP sink for alert/subscription tests |
| builder | - | Builds the driver jar |

Optional overlay profiles: **TLS/mTLS** and **OAuth2/Keycloak**.

### Optional TLS/mTLS profile

```bash
./scripts/generate_tls_certs.sh    # local CA + server cert + mTLS client cert into ./tls/
podman-compose -f docker-compose.yaml -f docker-compose.tls.yaml up -d
```

Adds `gizmosql-tls` (31338, CA-signed TLS) and `gizmosql-mtls` (31339,
requires client certificates), and mounts `./tls` into Metabase so the
driver's *Server CA certificate* and *mTLS client certificate/key* fields can
reference the files.

### Optional OAuth2 profile (Keycloak)

```bash
python scripts/generate_oauth_config.py    # deterministic RS256 signing key + Keycloak realm
podman-compose -f docker-compose.yaml -f docker-compose.oauth.yaml up -d keycloak gizmosql-oauth
```

Adds Keycloak (host port 8180, with client-credentials clients minting
`role=admin` and `role=readonly` tokens) and `gizmosql-oauth` (host port
31340; verifies JWT signature/issuer/audience). Connect from Metabase with
Username `token` and the OAuth access token as Password — the readonly-role
token is SELECT-only.

> Note: GizmoSQL **Core** accepts external JWTs only via that handshake
> convention. The JDBC `oauth.*` client-credentials flow fetches and sends the
> token correctly, but Core's bearer-header path only accepts its own session
> tokens (external bearer headers are an Enterprise/JWKS capability).

### CSV uploads

Uploads are double-gated: tick **"Writable backend (enable CSV uploads &
transforms)"** in the connection's advanced options, then pick the database
under **Admin → Settings → Uploads** (schema e.g. `main`). Uploading a CSV
creates a typed DuckDB table plus a Metabase model; appends via the table
menu work too.

## Configuration

- **Host**: (Default: localhost) – The GizmoSQL server's hostname or IP.
- **Port**: (Default: 31337) – GizmoSQL's default Flight SQL port.
- **Authentication** – controlled by the *"Authenticate with a token instead
  of username/password"* toggle:
  - *Toggle off (default)*: Username + Password → Flight handshake basic auth.
    - **GizmoSQL external JWT**: set Username to the literal `token`, JWT in
      Password.
  - *Toggle on*: Bearer token → sent as `Authorization: Bearer …`.
- **Catalog**: (Optional) – The catalog to scope sync to.
- **Schemas**: include/exclude patterns applied during sync.
- **Use Encryption**: (Default: true) – TLS on/off. Switch off for local
  plaintext servers (the docker-compose demo does this explicitly).
- **Disable Certificate Verification**: (Default: false) – Only for servers
  with self-signed certificates.
- **Advanced**: server CA certificate, mTLS client certificate/key (PEM
  secrets), connect timeout, writable-backend toggle, and free-form
  additional JDBC options (`threadPoolSize`, `retainAuth`, `oauth.*`, or any
  custom parameter — unknown parameters are forwarded to the server as gRPC
  headers).

## Project Structure

```
.
├── src/metabase/driver/       # Driver source code
│   └── gizmosql.clj
├── resources/                 # Plugin manifest
│   └── metabase-plugin.yaml
├── scripts/                   # Automation scripts
│   └── metabase_setup.py
├── gizmosql/                  # GizmoSQL configuration
│   └── init.sql               # Test data (sales, hr, analytics schemas)
├── test/                      # Metabase shared driver-harness tests
├── tests/e2e/                 # pytest end-to-end suite
├── docker-compose.yaml        # Container orchestration
└── CLAUDE.md                  # Development guide
```

## Testing

Two layers, both against a real GizmoSQL server:

- **Driver test suite** (every push/PR): CI starts a `gizmodata/gizmosql`
  service container and runs Metabase's shared driver harness — dataset
  loading over Flight SQL, validated sync, MBQL known-answer queries — plus
  unit tests for the connection-spec builder (`.github/workflows/build.yaml`).
- **End-to-end suite** (weekly + on demand): deploys the full compose stack
  and runs pytest against the live Metabase UI/API, covering connections and
  auth shapes, the connector option matrix, dashboards across visualization
  types, MBQL/segments/metrics/pivot, TLS/mTLS, OAuth, and uploads
  (`.github/workflows/e2e.yml`).

Locally:

```bash
# Clean start (removes all data)
podman compose down -v
podman compose up -d

# Wait for Metabase, then run setup
python scripts/metabase_setup.py

# Run the pytest e2e suite (see tests/e2e/README.md for optional stacks)
python -m pytest tests/e2e -v
```

If using Claude Code, run `/e2e-test` for guided end-to-end testing.

## Releases

Semantic versioning with `vX.Y.Z` tags. To cut a release: move the
`[Unreleased]` CHANGELOG section into a new version section, bump
`version.txt` (and `project.clj`), commit, then
`git push origin main vX.Y.Z`. The release workflow builds the per-Metabase
jars, extracts that CHANGELOG section as release notes, and publishes the
GitHub Release with the jars attached.

## Troubleshooting

### `Could not initialize class ...arrow.memory.RootAllocator`
Metabase is running on JDK 24+ (the v0.63 image ships JDK 25) without the
required Arrow JVM flags — see **Java / JVM requirements** above.

### `podman compose` fails with `root@127.0.0.1: Permission denied`
On Windows with Docker Desktop installed, `podman compose` delegates to
`docker-compose.exe` (an external compose provider) which tries to reach a
Docker host over SSH and fails. Use the pip-installed `podman-compose`
instead: `pip install podman-compose`, then `podman-compose up -d`.

### Check Metabase logs
```bash
podman compose logs metabase 2>&1 | tail -100
```

### Check connection pool status
```bash
podman compose logs metabase 2>&1 | grep "connections:"
```

### Rebuild driver after code changes
```bash
podman compose down metabase builder
podman compose up -d builder
# Wait ~30 seconds for build
podman compose up -d metabase
```

## License

Copyright © 2026 GizmoData LLC.
Portions copyright © 2025-2026 Georvic Tur (from the upstream
[metabase-flightsql-driver](https://github.com/J0hnG4lt/metabase-flightsql-driver)).

Licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). See [LICENSE](LICENSE).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
