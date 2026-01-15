from datetime import datetime
from zoneinfo import ZoneInfo   
from strava import get_activity_detail


# Helper to format seconds into HH:MM:SS
def format_seconds(sec):
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

# Helper to get activity name from sheet based on rules
def get_activity_name_from_sheet(activity_date, strava_name, sheet_lookup):
    """
    Returns the name of the activity from the sheet.
    - If Strava activity contains "Workout", return the 'gym' column.
    - If Strava activity contains "Run", return the 'treadmill' column.
    - Fall back to None if nothing matches or data is empty.
    """
    row = sheet_lookup.get(activity_date, {})

    if not row:
        return None

    if "Workout" in strava_name:
        gym_name = row.get("gym")
        if gym_name and gym_name != "-":
            return gym_name
    elif ("Run" in strava_name) or ("Walk" in strava_name):
        treadmill_name = row.get("treadmill")
        if treadmill_name and treadmill_name != "-":
            return treadmill_name

    # fallback: return Strava name itself if sheet data empty
    return strava_name

# Helper to extract and format the activity data we use
def return_activity_data(activity):
    detail = get_activity_detail(activity["id"])
    calories = detail.get("calories") or detail.get("total_calories") or "N/A"

    final_time = datetime.fromisoformat(activity["start_date"].replace("Z", "+00:00")) \
                        .astimezone(ZoneInfo("Europe/Athens")) \
                        .strftime("%Y-%m-%d %H:%M")

    activity_base = {
        "Name": activity.get("name"),
        "Start Date": final_time,#.isoformat(),  # store in local time
        "Duration": format_seconds(activity.get("elapsed_time")),
        "Heart Rate Avg": activity.get("average_heartrate"),
        "Heart Rate Max": activity.get("max_heartrate"),
        "Calories": calories
    }

    if ("Run" in activity.get("name")) or ("Walk" in activity.get("name")):
        activity_base["Distance"] = activity.get("distance")

    return activity_base

# Main function to match activities from Strava with names from the sheet
def matched_activities_from_sheet(activities, lookup):
    matched = []
    for act in activities:
        activity_data = return_activity_data(act)
        act_date = datetime.fromisoformat(activity_data.get("Start Date").replace("Z", "")).strftime("%Y-%m-%d")
        act_name = activity_data.get("Name")
        activity_data["Name"] = get_activity_name_from_sheet(act_date, act_name, lookup)
        matched.append(activity_data)
    return matched



