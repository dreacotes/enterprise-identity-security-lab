# Enterprise Identity Security Lab

A hands-on DevSecOps learning project built with Python, FastAPI,
Microsoft Entra ID, Docker, automated tests, and GitHub Actions.

## Current Status

- GET /health: public application health endpoint.
- GET /resources/{resource_id}: protected access to an in-memory sample resource.
- Microsoft Entra ID authentication using OAuth 2.0 Client Credentials.
- Resource access requires the Resources.Read application role.
- Fifteen automated tests covering API behavior and token validation.
- GitHub Actions runs Python tests, builds the Docker image, and checks container health.
- Docker container runs as a non-root user.
- Initial five-test version verified in a separate virtual environment.
- Automated deployment is planned.

Resource endpoints validate access tokens and enforce the required role.
The health endpoint remains public.

## Requirements

- Windows with PowerShell
- Python 3.15 (tested with 3.15.2)
- Git
- Docker Desktop with Linux containers, for Docker execution
- A Microsoft Entra tenant with access to configure app registrations and admin consent

## Set Up the Environment

From the project directory:

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configure Microsoft Entra ID

This lab uses two single-tenant app registrations in the same tenant.

### API Application

Register an application named enterprise-identity-api with:

- Supported account type: Single tenant.
- Application ID URI: api://<your-api-application-client-id>
- No redirect URI.
- Manifest setting api.requestedAccessTokenVersion set to 2.

Create an app role with:

- Display name: Read resources
- Allowed member types: Applications
- Value: Resources.Read
- Description: Allows an application to read API resources.
- Enabled: Yes

### Client Application

Register an application named enterprise-identity-client with:

- Supported account type: Single tenant.
- No redirect URI.
- Application permission: enterprise-identity-api → Resources.Read
- Tenant administrator consent granted for that permission.

Create a client credential for local token acquisition. Store the secret
securely and track its expiration. The secret Value is different from
the Secret ID.

The API does not need the client's secret.

### API Environment Variables

Before starting the API, set these variables in PowerShell:

```powershell
$env:ENTRA_TENANT_ID = "<your-lab-tenant-id>"
$env:ENTRA_AUDIENCE = "<your-api-application-client-id>"
```

Replace the placeholders with your tenant ID and API application ID.

ENTRA_AUDIENCE must contain the API application's client ID, without
the api:// prefix. Do not use the client application's ID.

These variables apply only to the current terminal and processes
started from it. Set them again when using a new terminal.

Never commit client secrets or access tokens.

### Token Acquisition

The client requests an access token from:

```text
https://login.microsoftonline.com/<your-lab-tenant-id>/oauth2/v2.0/token
```

The request uses:

- grant_type: client_credentials
- client_id: the client application's ID
- client_secret: the client secret Value
- scope: api://<your-api-application-client-id>/.default

Send the resulting access token in the request header:

```text
Authorization: Bearer <access-token>
```

The API validates the token signature, issuer, audience, lifetime,
tenant, and token version. It then requires Resources.Read in the roles claim.

## Run the API Locally

Configure the environment variables in the same terminal, then run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

- Health endpoint: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs
- Stop the server: Ctrl + C

Calling a resource endpoint requires a valid access token with Resources.Read.

## Run with Docker

Start Docker Desktop with Linux containers enabled.

Build the image from the project directory:

```powershell
docker build -t enterprise-identity-api:local .
```

Set ENTRA_TENANT_ID and ENTRA_AUDIENCE in the same terminal before
starting the container. Ensure port 8000 is not already used by a local server.

```powershell
docker run --rm --name identity-api -p 127.0.0.1:8000:8000 -e ENTRA_TENANT_ID -e ENTRA_AUDIENCE enterprise-identity-api:local
```

- Health endpoint: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

The application runs as appuser, a non-root user with UID 10001.
The published port is bound to the local computer only.

To run alongside a local server using port 8000, publish the container
on port 8001 instead:

```powershell
docker run --rm --name identity-api -p 127.0.0.1:8001:8000 -e ENTRA_TENANT_ID -e ENTRA_AUDIENCE enterprise-identity-api:local
```

Use http://127.0.0.1:8001 for that container.

Stop the container from another terminal:

```powershell
docker stop identity-api
```

The container is removed when stopped; the image remains available.
Rebuild the image after changing application code or dependencies.
Recreate the container after changing its environment variables.

## Run the Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Expected result: fifteen passing tests.

Tests run without a live Entra connection or real client credentials.
Uvicorn does not need to be running.

The suite covers:

- Public health endpoint and unknown routes.
- Resource lookup and input validation.
- HTTP 401 for a missing token.
- HTTP 403 for a missing application role.
- Acceptance of a correctly signed token.
- Rejection of a token signed with an incorrect key.
- Rejection of expired and not-yet-valid tokens.
- Rejection of incorrect issuer, audience, tenant, and token version.

Resource behavior tests override the authorization dependency.
Authorization tests simulate validated claims.
Cryptographic tests use temporary local RSA keys and execute the real
JWT signature and claim validation.

## Expected Behavior

| Request | Authentication | HTTP Status Code |
|---|---|---|
| GET /health | None | 200 |
| GET /resources/1 | Missing or invalid token | 401 |
| GET /resources/1 | Valid token without Resources.Read | 403 |
| GET /resources/1 | Valid token with Resources.Read | 200 |
| GET /resources/999 | Valid token with Resources.Read | 404 |
| GET /resources/abc | Valid token with Resources.Read | 422 |
| GET /no-existe | None | 404 |

If the API cannot retrieve signing keys from Entra when needed,
token verification returns HTTP 503.

Resources are stored in memory. The application does not use a database.

## Continuous Integration

The API tests workflow contains two jobs:

- test: installs dependencies and runs Pytest on Windows with Python 3.15.
- docker-build: builds the image on Linux, starts a container, and verifies
  that /health returns the expected JSON response.

The container job collects logs and removes the container after the check.
The image is not published to a registry.

The workflow runs when changes are pushed to main and when pull requests
targeting main are opened or updated. It can also be triggered manually
from Actions.

A failing test or build causes its job to fail.

The workflow is defined in .github/workflows/ci.yml.

The fifteen-test authentication update has passed locally. Its CI results
must be verified in the corresponding pull request.

## Installation Verification

The initial five-test version was verified in a separate virtual
environment created from requirements.txt.

The current fifteen-test version has been verified in the development
environment. Authenticated access with a real Entra token has also been
verified locally and inside Docker.

## Troubleshooting

- No module named: confirm that dependencies are installed in .venv.
- Error loading ASGI app: run the server from the directory containing main.py.
- Port already in use: stop the previous server or select a different host port.
- HTTP 401 without a token: provide an Authorization: Bearer header.
- HTTP 401 with a token: check token expiration, audience, issuer, tenant,
  version, and signature.
- HTTP 403: confirm that the token includes Resources.Read in its roles claim.
- HTTP 500 with a missing environment variable: set ENTRA_TENANT_ID and
  ENTRA_AUDIENCE before starting the API.
- Missing configuration in Docker: set the variables in the terminal used
  for docker run, pass them with -e, and recreate the container.
- HTTP 503 during token verification: check connectivity to the Entra
  signing-key endpoint.
- An existing image does not contain code changes: rebuild it and recreate
  the container.