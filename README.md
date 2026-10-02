# Decents Expense Calculation API

A FastAPI service for validating shared expenses and calculating member balances.
It uses selected expense calculation and validation code from Decents. Requests
include the items and members to calculate; the service does not store data.

## Run

Requirements: Docker with Compose, Python 3, and Git. Internet access is needed
to download images and packages. SonarScanner uses amd64 emulation on Apple Silicon.

From the repository directory:

```sh
python3 scripts/init-local.py
docker compose up -d --build
python3 scripts/manage.py setup-sonar
python3 scripts/manage.py update
python3 scripts/manage.py run
```

Wait for the Jenkins login page before running `manage.py update`. The first
start may take several minutes. Later runs can be started with **Build Now**.
Generated credentials are stored in the ignored `.env` file. Jenkins login is
`student`; SonarQube login is `admin`.

| Service | URL |
|---|---|
| Jenkins | http://localhost:18080/job/sit753-decents/ |
| SonarQube | http://localhost:19000/dashboard?id=sit753-decents |
| Test API | http://localhost:18081/docs |
| Production API | http://localhost:18082/docs |

The containers use fixed local names and ports. Run one checkout at a time.
To store local settings and build results elsewhere, use
`init-local.py --runtime-dir /path/to/runtime`, pass that directory's `.env` to
Compose with `--env-file`, and to `manage.py` with `--env-file`.

## API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Service status and environment name |
| `POST /items/validate` | Validate expense or transfer data |
| `POST /balances/calculate` | Calculate each member's credits, debts, and net balance |

Calculations support weighted splits, supplied exchange rates, and decimal
rounding. Exchange rates are supplied by the caller; the service does not fetch
live rates. Invalid requests return HTTP 422.

Examples are in `app/examples`. Use them in Swagger **Try it out**, or run:

```sh
curl http://localhost:18081/health
curl -H 'Content-Type: application/json' --data-binary @app/examples/item.json http://localhost:18081/items/validate
curl -H 'Content-Type: application/json' --data-binary @app/examples/balances.json http://localhost:18082/balances/calculate
```

The example splits AUD 120 equally between Alice and Bob. Alice pays the full
amount, so her net balance is -60 (receivable), and Bob's is 60 (payable).

## Pipeline

| Stage | Action |
|---|---|
| Build | Build and tag the Docker image; save it as an artifact |
| Test | Run component and HTTP tests against the built API |
| Code Quality | Analyze code and coverage with SonarQube; wait for the quality gate |
| Security | Scan installed dependencies and the image with Trivy |
| Deploy | Deploy to test; verify health and a balance calculation |
| Release | Promote the same image to local production and verify it |

Tests, the quality gate, and security checks stop the pipeline on failure.
Test and production use separate containers, environment names, and ports.
The image is not rebuilt between testing and release. Jenkins archives test
results, coverage, scan reports, deployment checks, and the image.

The quality gate requires maintainability B or better, reliability C or better,
and duplication at most 10%. New-code conditions also check issues, coverage,
and duplication. Metrics and gate results are available in SonarQube and the
build artifacts. Builds start manually; no Git push trigger is configured.

Release can restore the previous image if the new production container fails
startup checks. This fallback has not been verified with a simulated failure.

## Tests

The suite covers expense and transfer validation, weighted balances, exchange
rate conversion, rounding, and HTTP responses. HTTP cases run both in process
and against the running container. Test reports apply to this API's scope.

## Security

Trivy reports vulnerability IDs, severity, installed versions, and fixed versions.
Unaccepted HIGH and CRITICAL findings block the pipeline.

`security-exceptions.json` lists specific OS packages with no fixed version in
the recorded scan, reasons, references, and expiry dates. Only matching OS HIGH
findings can be accepted. Available fixes, expired exceptions, and CRITICAL
findings still block. These exceptions are limited to local containers.

The API runs as a non-root user, with capabilities dropped and no-new-privileges.
It has no host mounts or Docker socket, and its ports are exposed on localhost.
These measures reduce risk; they do not fix the vulnerable packages.

## Results and shutdown

```sh
python3 scripts/manage.py status
python3 scripts/manage.py log
docker compose stop
docker stop sit753-decents-test sit753-decents-prod
```

Reports are in the runtime directory's `workspace/results` and Jenkins artifacts.
The pipeline creates the API containers separately from the supporting Compose
services, so stop them with the final command.
