from datetime import datetime
import requests

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
app_version = '2.70.0'
device_model = 'Windows'

session = None

def get_oauth_token():
    """
    Get an OAuth token from the Vinted API.

    Returns:
        dict: OAuth token information
    """
    response = requests.post(
        url='https://www.vinted.fr/api/v2/oauth/token',
        headers={
            'User-Agent': user_agent,
            'x-app-version': app_version,
            'x-device-model': device_model,
            'short-bundle-version': app_version,
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        data={
            'grant_type': 'client_credentials',
            'client_id': 'YOUR_CLIENT_ID',
            'client_secret': 'YOUR_CLIENT_SECRET'
        }
    )

    if response.status_code != 200:
        return False

    return response.json()
