from google_sheets import GoogleSheetAuth,Chart,ensure_or_create_sheet,build_sheet_lookup,fix_format_of_sheet_data,insert_activity_table,get_last_activity_row
from strava import get_activities_from_strava_api, matched_activities_from_sheet
from datetime import datetime, timezone
import os
import os
import sys
import traceback

def log(msg: str):
    """Minimal timestamped log with UTC timezone."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] {msg}")

if __name__ == "__main__":
    try:
        #file name of the whole sheet
        google_sheet_file_name = os.environ.get("GOOGLE_SHEET_FILE")

        #the name of the graph sheet to ensure/create/use
        graphs_sheet_name = os.environ.get("GRAPHS_SHEET_NAME")

        # 1. Connect to Google Sheet
        gs = GoogleSheetAuth("/app/src/credentials/google_creds.json", google_sheet_file_name)
        sheet1 = gs.get_sheet()  
        #get a lookup dictionary for activities names from sheet1
        lookup = build_sheet_lookup(sheet1)
        
        # 2. Fix format of Sheet1 data
        if not fix_format_of_sheet_data(sheet1):
            log(f"Failed to format data in sheet.")

        # 3. Ensure 'graphs' sheet exists
        if not ensure_or_create_sheet(gs.spreadsheet, graphs_sheet_name):
            log(f"Failed to create {graphs_sheet_name} sheet.")

        graphs_sheet = gs.spreadsheet.worksheet(graphs_sheet_name)

        # 4. Create Weight to Date graph
        weight_to_date_graph = Chart(
            chart_type="line",
            chart_name="Weight over Time",
            chart_style="smooth",
            origin_sheet=sheet1,
            target_sheet=graphs_sheet,
            x_column="A",
            y_column="D"
        )

        #weekly charts
        #if not weight_to_date_graph.create_chart(gs.service, gs.spreadsheet_id, 0, 0, weekly=True):
        #    print(f"Failed to create weekly charts.")
        
        #total charts
        if not weight_to_date_graph.create_chart(gs.service, gs.spreadsheet_id, 0, 0):
            log(f"Failed to insert chart '{weight_to_date_graph.chart_name}' into sheet.")

        # 5. Fetch recent activities from Strava and create activity tables
        #getting the last 2 activities from strava api
        activities = get_activities_from_strava_api(limit=5)
        #matching them with the activities name from the sheet for that specific date
        matched_activities = matched_activities_from_sheet(activities, lookup)
        
        #today's date
        today = datetime.now(timezone.utc).date()

        # Insert activity tables into 'graphs' sheet
        starting_col = 1
        col_step = 3  # space between tables
        next_table_row = get_last_activity_row(graphs_sheet,21) + 2  # leave a gap of 1 row
        added_count = 0

        #get existing dates to avoid duplicates
        #existing_dates_of_activities = [cell.value for cell in graphs_sheet.range("B1:B1000") if cell.value]
        existing_dates_of_activities = [
            cell.value
            for cell in graphs_sheet.range("B1:B1000") + graphs_sheet.range("E1:E1000")
            if cell.value
        ]

        for activity in matched_activities:
            activity_date = datetime.fromisoformat(activity.get("Start Date")).date()

            # Skip if not today's activity
            if activity_date != today:
                continue

            # Skip if activity already exists
            if activity.get("Start Date") in existing_dates_of_activities:
                log(f"Skipping duplicate activity: '{activity.get('Name')}' at {activity.get('Start Date')}")
                continue

            col = starting_col + added_count * col_step
            insert_activity_table(sheet=graphs_sheet, row=next_table_row, col=col, activity=activity)
            added_count += 1

        log(f"'{graphs_sheet_name}' sheet of '{google_sheet_file_name}' file updated. {added_count} activity table(s) added.")


    except Exception:
        log("Error occurred during execution:")
        traceback.print_exc(file=sys.stdout)