import time
import requests
import configparser
import os
from zoneinfo import ZoneInfo
from datetime import datetime

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials", "strava_creds.ini")
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

CLIENT_ID = config["STRAVA"]["client_id"]
CLIENT_SECRET = config["STRAVA"]["client_secret"]
ACCESS_TOKEN = config["STRAVA"]["access_token"]
REFRESH_TOKEN = config["STRAVA"]["refresh_token"]
EXPIRES_AT = int(config["STRAVA"]["expires_at"])

# Save updated tokens back to ini
def save_tokens():
    config["STRAVA"]["access_token"] = ACCESS_TOKEN
    config["STRAVA"]["refresh_token"] = REFRESH_TOKEN
    config["STRAVA"]["expires_at"] = str(EXPIRES_AT)
    with open(CONFIG_PATH, "w") as f:
        config.write(f)

# Refresh token if expired
def refresh_token_if_needed():
    global ACCESS_TOKEN, REFRESH_TOKEN, EXPIRES_AT
    now = int(time.time())
    if now >= EXPIRES_AT:
        print("Access token expired, refreshing...")
        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": REFRESH_TOKEN
            }
        )
        data = response.json()
        ACCESS_TOKEN = data["access_token"]
        REFRESH_TOKEN = data["refresh_token"]
        EXPIRES_AT = data["expires_at"]
        print("Token refreshed successfully!")
        save_tokens()


# Fetch recent activities
def get_activities_from_strava_api(limit=10):
    refresh_token_if_needed()
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers=headers,
        params={"per_page": limit, "page": 1}
    )
    if response.status_code != 200:
        print("Error fetching activities:", response.text)
        return []
    return response.json()

# Fetch detailed activity info
def get_activity_detail(activity_id):
    refresh_token_if_needed()
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = requests.get(
        f"https://www.strava.com/api/v3/activities/{activity_id}",
        headers=headers
    )
    if response.status_code != 200:
        print(f"Error fetching details for activity {activity_id}:", response.text)
        return {}
    return response.json()
