import gspread
from gspread_formatting import *
import pandas as pd

# Utility functions for Google Sheets operations
def fix_format_of_sheet_data(sheet):
    """
    Cleans Sheet1 data in-place:
    - Column A: proper date format (yyyy-mm-dd) if it's a date
    - Column D: numeric weight (float) if it exists
    Leaves other columns untouched, and preserves non-date rows like month names.
    Returns True if successful, False if an error occurred.
    """
    try:
        data = sheet.get_all_values()
        if not data or len(data) < 2:
            return False

        # Skip header
        rows = data[1:]

        # Prepare lists for batch update
        date_updates = []
        weight_updates = []

        for i, row in enumerate(rows):
            # Default values (no change)
            date_to_write = row[0] if len(row) > 0 else ""
            weight_to_write = row[3] if len(row) > 3 else ""

            # --- Clean Date (Column A) if it's a date ---
            date_val = row[0].strip() if len(row) > 0 else ""
            try:
                if "/" in date_val:
                    date = pd.to_datetime(date_val, format="%d/%m/%y", errors='raise')
                else:
                    date = pd.to_datetime(date_val, format="%Y-%m-%d", errors='raise')
                date_to_write = date.strftime("%Y-%m-%d")
            except Exception as e:
                pass  # leave original (could be month name or invalid)

            # --- Clean Weight (Column D) ---
            weight_val = row[3].replace(",", ".").strip() if len(row) > 3 else ""
            try:
                weight = float(weight_val)
                weight_to_write = f"{weight:.1f}"
            except Exception:
                pass  

            date_updates.append([date_to_write])
            weight_updates.append([weight_to_write])

        # Batch update dates in column A
        sheet.update(f"A2:A{len(date_updates)+1}", date_updates)
        # Batch update weights in column D
        sheet.update(f"D2:D{len(weight_updates)+1}", weight_updates)

        return True
    except Exception as e:
        print(f"Error cleaning sheet data: {e}")
        return False

# Helper to get a lookup dict from the sheet data
def build_sheet_lookup(sheet):
    """
    Builds a dict:
    {
        "2025-09-16": { "gym": "...", "treadmill": "...", "weight": "...", "sleep": "...", "water": "..." },
    }
    """
    data = sheet.get_all_records()
    lookup = {}

    for row in data:
        date = str(row.get("Ημερομηνία")).strip()
        if not date or date == "nan":
            continue

        lookup[date] = {
            "gym": (row.get("Γυμναστήριο") or "").strip(),
            "treadmill": (row.get("Διάδρομος") or "").strip(),
            "weight": (row.get("Βάρος") or "").strip(),
            "sleep": (row.get("Ύπνος") or "").strip(),
            "water": (row.get("Νερό") or "").strip(),
        }

    return lookup

# Helper to ensure or create a sheet
def ensure_or_create_sheet(spreadsheet, sheet_name: str) -> bool:
    """
    Ensures that a sheet with `sheet_name` exists in the spreadsheet.
    If it exists, do nothing. If not, create it.
    Returns True if sheet exists or is created successfully.
    Returns False only if an unexpected error occurs.
    """
    try:
        # Try to get the sheet
        try:
            spreadsheet.worksheet(sheet_name)
            return True  # Sheet already exists
        except gspread.exceptions.WorksheetNotFound:
            # Sheet doesn't exist, create it
            spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="1000")
            return True
    except Exception as e:
        print(f"Error ensuring/creating sheet '{sheet_name}': {e}")
        return False

# Helper to insert an activity table
def insert_activity_table(sheet, row, col, activity):
    """
    Insert an activity as a 2-column table starting at (row, col) in the given sheet.
    Uses batch_update to minimize API calls. Applies formatting: column widths, header color, text alignment, borders.
    row/col are 1-based (like in Google Sheets).
    """
    from gspread.utils import rowcol_to_a1

    # Determine metrics dynamically
    metrics = [
        ("Date", activity.get("Start Date", "")),
        ("Duration", activity.get("Duration", "")),
        ("Avg HR", f"{activity.get('Heart Rate Avg', 0):.0f} bpm"),
        ("Max HR", f"{activity.get('Heart Rate Max', 0):.0f} bpm"),
        ("Calories", f"{activity.get('Calories', 0):.0f}")
    ]

    # Add distance for treadmill/run activities
    if "Distance" in activity:
        metrics.insert(4, ("Distance", f"{activity['Distance']/1000:.2f} km"))

    num_rows = len(metrics)

    # SheetId is required for batchUpdate
    sheet_id = sheet._properties['sheetId']

    # Convert 1-based row/col to 0-based for batchUpdate
    r = row - 1
    c = col - 1

    # Determine header color
    if "Distance" in activity:
        header_color = {"red": 1, "green": 1, "blue": 0.6}  # light yellow for treadmill
    else:
        header_color = {"red": 0.8, "green": 0.9, "blue": 1}  # light blue for gym

    requests = []

    # Clear table area
    requests.append({
        "updateCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": r,
                "endRowIndex": r + num_rows + 1,  # +1 for header
                "startColumnIndex": c,
                "endColumnIndex": c + 2
            },
            "fields": "userEnteredValue"
        }
    })

    # Merge header (1 row x 2 columns)
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": r,
                "endRowIndex": r + 1,
                "startColumnIndex": c,
                "endColumnIndex": c + 2
            },
            "mergeType": "MERGE_ALL"
        }
    })

    # Header value and formatting
    requests.append({
        "updateCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": r,
                "endRowIndex": r + 1,
                "startColumnIndex": c,
                "endColumnIndex": c + 2
            },
            "rows": [{
                "values": [{
                    "userEnteredValue": {"stringValue": activity.get("Name", "Activity")},
                    "userEnteredFormat": {
                        "backgroundColor": header_color,
                        "horizontalAlignment": "CENTER",
                        "textFormat": {"bold": True, "fontSize": 12}
                    }
                }]
            }],
            "fields": "userEnteredValue,userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    })

    # Metrics rows
    metric_rows = []
    for label, value in metrics:
        metric_rows.append({
            "values": [
                {"userEnteredValue": {"stringValue": label}},
                {"userEnteredValue": {"stringValue": value},
                 "userEnteredFormat": {"horizontalAlignment": "CENTER"}}
            ]
        })

    requests.append({
        "updateCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": r + 1,  # after header
                "endRowIndex": r + 1 + num_rows,
                "startColumnIndex": c,
                "endColumnIndex": c + 2
            },
            "rows": metric_rows,
            "fields": "userEnteredValue,userEnteredFormat(horizontalAlignment)"
        }
    })

    # Borders
    requests.append({
        "updateBorders": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": r,
                "endRowIndex": r + num_rows + 1,
                "startColumnIndex": c,
                "endColumnIndex": c + 2
            },
            "top": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
            "bottom": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
            "left": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
            "right": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}}
        }
    })

    # Column widths
    requests.append({
        "updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": c, "endIndex": c + 1},
            "properties": {"pixelSize": 120},
            "fields": "pixelSize"
        }
    })
    requests.append({
        "updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": c + 1, "endIndex": c + 2},
            "properties": {"pixelSize": 150},
            "fields": "pixelSize"
        }
    })

    # Execute all at once
    sheet.spreadsheet.batch_update({"requests": requests})

# Helper to get the last activity row
def get_last_activity_row(sheet, start_row=43):
    """
    Returns the row index where the last activity table ends.
    Looks for the last non-empty row in column 1 starting from start_row.
    """
    # Get all values in column A
    col_values = sheet.col_values(1)  # 1-based indexing for gspread

    # Filter rows starting at start_row
    relevant_rows = col_values[start_row-1:]  # adjust 0-based index

    last_row = start_row - 1  # default if nothing found
    for i, val in enumerate(relevant_rows):
        if val.strip():  # non-empty
            last_row = start_row + i

    # Assuming each table has num_rows = 6 (or dynamically calculated)
    return last_row
