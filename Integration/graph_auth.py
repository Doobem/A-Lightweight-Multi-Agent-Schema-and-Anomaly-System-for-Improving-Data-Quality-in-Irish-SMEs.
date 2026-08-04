import os
import requests
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
SCOPE = "https://graph.microsoft.com/.default"

# ---------------------------------------------------------
# AUTH — CLIENT CREDENTIALS FLOW (NO USER LOGIN)
# ---------------------------------------------------------
def get_access_token():
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": SCOPE,
        "grant_type": "client_credentials"
    }

    response = requests.post(TOKEN_URL, data=data)

    if response.status_code != 200:
        raise Exception(f"Token request failed: {response.status_code} - {response.text}")

    return response.json()["access_token"]
