# Enterprise Identity Security Lab

A hands-on DevSecOps learning project built with Python, FastAPI,
automated tests, and GitHub Actions.

## Current Status

- GET /health: confirms that the application responds.
- GET /resources/{resource_id}: retrieves an in-memory sample resource.
- Five automated tests using Pytest.
- Continuous integration using GitHub Actions.
- Dependency installation verified in a separate virtual environment.
- Docker image built and verified locally, running as a non-root user.
- Authentication and automated deployment are planned.

The API does not yet implement authentication or authorization.

## Requirements

- Windows with PowerShell
- Python 3.15 (tested with 3.15.2)
- Git

## Set Up the Environment

From the project directory:

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the API Locally

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

- Health endpoint: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs
- Stop the server: Ctrl + C

## Run with Docker

Requires Docker Desktop running with Linux containers.

Build the image from the project directory:

```powershell
docker build -t enterprise-identity-api:local .
```

Start the container:

```powershell
docker run --rm --name identity-api -p 127.0.0.1:8000:8000 enterprise-identity-api:local
```

Open http://127.0.0.1:8000/health or http://127.0.0.1:8000/docs.

The application runs as a non-root user. The published port is bound
to the local computer only.

Stop the container from another terminal:

```powershell
docker stop identity-api
```

The container is removed when stopped; the image remains available.
Rebuild the image after changing application code or dependencies.

## Run the Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Expected result: five passing tests.

The tests use TestClient, so Uvicorn does not need to be running.

## Expected Behavior

| Request | HTTP Status Code |
|---|---|
| GET /health | 200 |
| GET /resources/1 | 200 |
| GET /resources/999 | 404 |
| GET /resources/abc | 422 |
| GET /no-existe | 404 |

Resources are stored in memory. The application does not use a database.

## Continuous Integration

The API tests workflow installs dependencies and runs all five tests
with Pytest on a temporary Windows runner using Python 3.15.

It runs when changes are pushed to main and when pull requests targeting
main are opened or updated. It can also be triggered manually from Actions.

A failing test causes the workflow run to fail.

The workflow is defined in .github/workflows/ci.yml.

## Installation Verification

Dependencies were installed from requirements.txt in a separate virtual
environment created from scratch. All five tests passed in that environment.

## Troubleshooting

- No module named: confirm that dependencies are installed in .venv.
- Error loading ASGI app: run the server from the directory containing main.py.
- Port 8000 already in use: stop the previous server or use --port 8001.