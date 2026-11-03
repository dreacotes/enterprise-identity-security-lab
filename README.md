# Enterprise Identity Security Lab

A hands-on DevSecOps learning project built with Python, FastAPI,
Microsoft Entra ID, Docker, automated tests, and GitHub Actions.

## Current Status

- Public health endpoint: GET /health.
- Protected resource endpoint: GET /resources/{resource_id}.
- Application access using OAuth 2.0 Client Credentials.
- Interactive user sign-in using MSAL, OpenID Connect, and Authorization Code with PKCE.
- Application authorization through the Resources.Read app role.
- Delegated authorization through the Resources.Read.Delegated scope.
- Twenty-seven automated tests covering API behavior, token validation,
  and authentication configuration errors.
- GitHub Actions runs Python tests, builds the Docker image, and checks container health.
- Docker container runs as a non-root user.
- Controlled HTTP 503 responses for missing or malformed authentication configuration.
- Automated deployment is planned.

Resources are stored in memory. The application does not use a database.

## Requirements

- Windows with PowerShell
- Python 3.15 (tested with 3.15.2)
- Git
- Docker Desktop with Linux containers, for Docker execution
- A Microsoft Entra tenant with permission to configure app registrations
  and grant administrator consent

## Set Up the Environment

From the project directory:

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configure Microsoft Entra ID

This lab uses three single-tenant app registrations in the same tenant:

| Application | Purpose |
|---|---|
| enterprise-identity-api | Represents the protected API |
| enterprise-identity-client | Calls the API without a signed-in user |
| enterprise-identity-user-client | Signs in a user and calls the API on their behalf |

### API Application

Register enterprise-identity-api with:

- Supported account type: Single tenant.
- Application ID URI: api://<your-api-application-client-id>
- No redirect URI.
- Manifest setting api.requestedAccessTokenVersion set to 2.

Create an app role:

| Setting | Value |
|---|---|
| Display name | Read resources |
| Allowed member types | Applications |
| Value | Resources.Read |
| Description | Allows an application to read API resources. |
| Enabled | Yes |

Under Expose an API, create a delegated scope:

| Setting | Value |
|---|---|
| Scope name | Resources.Read.Delegated |
| Who can consent? | Admins only |
| Admin consent display name | Read resources as the signed-in user |
| Admin consent description | Allows the client to read API resources on behalf of the signed-in user. |
| State | Enabled |

The full delegated scope is:

```text
api://<your-api-application-client-id>/Resources.Read.Delegated
```

### Application Client

Register enterprise-identity-client with:

- Supported account type: Single tenant.
- No redirect URI.
- Application permission: enterprise-identity-api → Resources.Read
- Administrator consent granted for that permission.

Create a client credential for local token acquisition. Store the secret
securely and track its expiration.

Use the client secret Value, not the Secret ID.

The API does not need the client's secret.

### Interactive User Client

Register enterprise-identity-user-client with:

- Supported account type: Single tenant.
- Platform: Mobile and desktop applications / public native client.
- Redirect URI: http://localhost
- Delegated permission: enterprise-identity-api → Resources.Read.Delegated
- Administrator consent granted for that permission.

This client does not use a client secret.

## Configure the API Environment

Before starting the API, set these variables in PowerShell:

```powershell
$env:ENTRA_TENANT_ID = "<your-lab-tenant-id>"
$env:ENTRA_AUDIENCE = "<your-api-application-client-id>"
```

Replace the placeholders with your tenant ID and API application ID.
Both values must have a valid UUID format.

ENTRA_AUDIENCE must contain the API application's client ID, without
the api:// prefix. Do not use either client application's ID.

Environment variables apply only to the current terminal and processes
started from it. Configure them again when opening a new terminal.

Authentication configuration is loaded when token validation is needed.
Missing or malformed values produce a controlled HTTP 503 response.
The health endpoint remains available.

Restart the server or recreate the container after changing its
authentication configuration.

Never commit client secrets or access tokens.

## Run the API Locally

Configure the API environment variables in the same terminal, then run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

- Health endpoint: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs
- Stop the server: Ctrl + C

The health endpoint is public. Resource endpoints require an authorized
access token.

## Application-to-Application Access

The application client requests an access token from:

```text
https://login.microsoftonline.com/<your-lab-tenant-id>/oauth2/v2.0/token
```

The request uses:

| Parameter | Value |
|---|---|
| grant_type | client_credentials |
| client_id | Application ID of enterprise-identity-client |
| client_secret | Client secret Value |
| scope | api://<your-api-application-client-id>/.default |

Send the access token in the request header:

```text
Authorization: Bearer <access-token>
```

The API validates the token and requires Resources.Read in its roles claim.

## Sign In as a User

Start the API locally on port 8000 in one terminal.

In a second PowerShell terminal, configure:

```powershell
$env:ENTRA_TENANT_ID = "<your-lab-tenant-id>"
$env:ENTRA_AUDIENCE = "<your-api-application-client-id>"
$env:ENTRA_USER_CLIENT_ID = "<your-user-client-application-id>"
```

ENTRA_USER_CLIENT_ID must contain the Application ID of
enterprise-identity-user-client.

Run:

```powershell
.\.venv\Scripts\python.exe login_user.py
```

The program opens the browser and uses MSAL interactive authentication
with Authorization Code and PKCE. Sign in with an account that has access
to the lab tenant.

After sign-in, the program sends the access token to:

```text
http://127.0.0.1:8000/resources/1
```

Expected output includes:

```text
Login successful.
API status: 200
API response: {'id': 1, 'name': 'Identity security lab'}
```

The program does not print tokens or persist them to disk.

The API receives an access token, not an ID token. For delegated tokens,
it requires Resources.Read.Delegated in the scp claim.

## Authorization Rules

The API validates:

- RS256 token signature using Microsoft's public signing keys.
- Expected issuer and audience.
- Token expiration and validity times.
- Expected tenant.
- Token version 2.0.

After token validation:

- If scp is present, the token must include the exact
  Resources.Read.Delegated scope.
- If scp is absent, the token must include the Resources.Read app role.
- An application role cannot bypass an incorrect delegated scope.

A valid signature alone does not grant access.

## Run with Docker

Start Docker Desktop with Linux containers enabled.

Build the image from the project directory:

```powershell
docker build -t enterprise-identity-api:local .
```

Set ENTRA_TENANT_ID and ENTRA_AUDIENCE in the same terminal before starting
the container. Ensure port 8000 is not already used by a local server.

```powershell
docker run --rm --name identity-api -p 127.0.0.1:8000:8000 -e ENTRA_TENANT_ID -e ENTRA_AUDIENCE enterprise-identity-api:local
```

- Health endpoint: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

The application runs as appuser, a non-root user with UID 10001.
The published port is bound to the local computer only.

To run alongside a local server using port 8000, use port 8001:

```powershell
docker run --rm --name identity-api -p 127.0.0.1:8001:8000 -e ENTRA_TENANT_ID -e ENTRA_AUDIENCE enterprise-identity-api:local
```

Use http://127.0.0.1:8001 for that container.

The login_user.py script currently calls port 8000. To use it with Docker,
run the container on host port 8000 and stop any local server using that port.

Stop the container from another terminal:

```powershell
docker stop identity-api
```

The container is removed when stopped; the image remains available.

Rebuild the image after changing application code or dependencies.
Recreate the container after changing its environment variables.

The interactive login script runs on the host computer, not inside
the API container.

## Run the Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Expected result: twenty-seven passing tests.

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
- Acceptance of the required delegated scope.
- Rejection of incorrect or partially matching delegated scopes.
- Prevention of role-based bypass when a delegated scope is incorrect.
- HTTP 503 for missing, empty, or malformed authentication configuration.
- Availability of the health endpoint without authentication configuration.
- Controlled HTTP 503 from a protected route when configuration is missing.

Resource behavior tests override the authorization dependency.
Authorization tests simulate validated claims.

Cryptographic tests use temporary local RSA keys and execute the real
JWT signature and claim validation.

The interactive browser login is verified manually; it is not automated
by these tests.

## Expected Behavior

For resource requests, an authorized token means either an application
token with Resources.Read or a delegated token with Resources.Read.Delegated.

| Request | Authentication and Configuration | HTTP Status Code |
|---|---|---|
| GET /health | No token required, including when auth configuration is missing | 200 |
| GET /resources/1 | Missing token | 401 |
| GET /resources/1 | Invalid token with valid auth configuration | 401 |
| GET /resources/1 | Valid token without the required permission | 403 |
| GET /resources/1 | Authorized token | 200 |
| GET /resources/999 | Authorized token | 404 |
| GET /resources/abc | Authorized token | 422 |
| GET /resources/1 | Bearer credential supplied, but auth configuration is missing or malformed | 503 |
| GET /no-existe | No token required | 404 |

If the API cannot retrieve signing keys from Entra when needed,
token verification returns HTTP 503.

GET /health confirms that the application responds. It does not verify
that Entra configuration or connectivity is ready.

## Continuous Integration

The workflow contains two jobs:

| Job | Checks |
|---|---|
| test | Installs dependencies and runs Pytest on Windows with Python 3.15 |
| docker-build | Builds the image on Linux, starts a container, and verifies the health response |

The container job collects logs and removes the container after the check.
The image is not published to a registry.

The workflow runs when changes are pushed to main and when pull requests
targeting main are opened or updated. It can also be triggered manually
from Actions.

A failing test or build causes its job to fail.

The workflow is defined in .github/workflows/ci.yml.

CI does not perform interactive user login or use real client secrets.
The configuration-error update has passed all twenty-seven tests locally;
its CI results still need to be verified in the corresponding pull request.

## Verification History

- The initial five-test version was verified in a separate virtual
  environment created from requirements.txt.
- Application access using a real Entra token was verified locally
  and inside Docker.
- The nineteen-test delegated-access version passed locally and both
  pull request CI jobs succeeded.
- Interactive user login and delegated API access returned HTTP 200
  against the local Python server.
- Interactive delegated access inside Docker has not yet been
  manually verified.
- The current configuration-error update passed twenty-seven tests
  in the development environment.

## Troubleshooting

- No module named: confirm that dependencies are installed in .venv.
- Error loading ASGI app: run the server from the directory containing main.py.
- Missing environment variable in the login script: configure all three
  variables in the terminal used to execute login_user.py.
- Missing ENTRA_USER_CLIENT_ID: use the Application ID of
  enterprise-identity-user-client.
- Port already in use: stop the previous server or select a different host port.
- Cannot connect to the local API: confirm that the server is running
  on port 8000 before executing login_user.py.
- HTTP 401 without a token: provide an Authorization: Bearer header.
- HTTP 401 with a token: check expiration, audience, issuer, tenant,
  version, and signature.
- HTTP 403 with an application token: check Resources.Read in roles.
- HTTP 403 with a delegated token: check Resources.Read.Delegated in scp.
- HTTP 503 with "Authentication service is not configured correctly":
  set ENTRA_TENANT_ID and ENTRA_AUDIENCE to valid UUIDs in the terminal
  used to start the API, then restart the server or recreate the container.
- Missing configuration in Docker: set the variables in the terminal used
  for docker run, pass them with -e, and recreate the container.
- HTTP 503 with "Token verification service unavailable": check connectivity
  to the Entra signing-key endpoint.
- Old behavior in Docker: rebuild the image and recreate the container.