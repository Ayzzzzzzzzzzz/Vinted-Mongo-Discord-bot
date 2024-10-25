import requests
from datetime import datetime

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
app_version = '2.57.0'
device_model = 'Windows'

session = None

def get_oauth_token():
    """
    Get an OAuth token from the Vinted API.

    Returns:
        dict: The OAuth token response.
    """
    response = requests.post(
        url='https://www.vinted.fr/api/v2/oauth/token',
        data={
            'grant_type': 'client_credentials',
            'client_id': 'your_client_id',
            'client_secret': 'your_client_secret'
        },
        headers={
            'User-Agent': user_agent,
            'x-app-version': app_version,
            'x-device-model': device_model,
            'short-bundle-version': app_version,
            'Accept': 'application/json'
        }
    )

    if response.status_code != 200:
        return None

    return response.json()
