import httpx

import os

import msal


def main():
    tenant_id = os.environ["ENTRA_TENANT_ID"]
    api_id = os.environ["ENTRA_AUDIENCE"]
    client_id = os.environ["ENTRA_USER_CLIENT_ID"]

    client = msal.PublicClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
    )

    result = client.acquire_token_interactive(
        scopes=[f"api://{api_id}/Resources.Read.Delegated"],
        prompt="select_account",
        timeout=180,
    )

    if "access_token" not in result:
        print("Login failed:", result.get("error"))
        print(result.get("error_description", "No details available"))
        return

    print("Login successful.")
    print("Token type:", result.get("token_type"))
    print("Granted scopes:", result.get("scope"))

    try:
        response = httpx.get(
            "http://127.0.0.1:8000/resources/1",
            headers={
                "Authorization": f"Bearer {result['access_token']}",
            },
            timeout=15,
        )
    except httpx.RequestError:
        print("Cannot connect to the local API.")
        return

    print("API status:", response.status_code)
    print("API response:", response.json())


if __name__ == "__main__":
    main()