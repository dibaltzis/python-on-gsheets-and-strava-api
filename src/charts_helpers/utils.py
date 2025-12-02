from googleapiclient.errors import HttpError
from datetime import datetime
from datetime import datetime, timedelta
import itertools

# Helper to get contiguous data ranges
def get_contiguous_ranges(sheet, x_column, y_column):
    """
    Returns x_range and y_range dictionaries ready for Google Sheets API,
    based on contiguous rows with valid data in x and y columns.
    Returns None if no valid data found.
    """
    values = sheet.get_all_values()
    first_row = None
    last_row = None

    for idx, row in enumerate(values[1:], start=2):
        date_val = row[0].strip() if len(row) > 0 else ""
        y_val = row[ord(y_column) - ord("A")].strip() if len(row) > ord(y_column) - ord("A") else ""

        try:
            datetime.strptime(date_val, "%Y-%m-%d")
        except:
            continue
        if not y_val:
            continue

        if first_row is None:
            first_row = idx
        last_row = idx

    if first_row is None or last_row is None:
        return None

    first_row_idx = first_row - 1
    last_row_idx = last_row
    x_col_idx = ord(x_column) - ord("A")
    y_col_idx = ord(y_column) - ord("A")

    x_range = {
        "sheetId": sheet.id,
        "startRowIndex": first_row_idx,
        "endRowIndex": last_row_idx,
        "startColumnIndex": x_col_idx,
        "endColumnIndex": x_col_idx + 1
    }

    y_range = {
        "sheetId": sheet.id,
        "startRowIndex": first_row_idx,
        "endRowIndex": last_row_idx,
        "startColumnIndex": y_col_idx,
        "endColumnIndex": y_col_idx + 1
    }

    return x_range, y_range, {"first_row": first_row_idx, "last_row": last_row_idx, "y_col": y_col_idx}

# Helper to compute y-axis window
def compute_y_axis_window(sheet, range_info, padding=1.5):
    values = sheet.get_all_values()
    y_values = []

    for row in values[1:]:
        if len(row) > range_info["y_col"]:
            val = row[range_info["y_col"]].strip()
            if val:
                try:
                    y_values.append(float(val))
                except:
                    pass

    if not y_values:
        return 0, 100

    return max(0, min(y_values) - padding), max(y_values) + padding

# Helper to find existing chart by name
def find_existing_chart_id(service, spreadsheet_id, chart_name):
    try:
        sheets = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            includeGridData=False
        ).execute().get("sheets", [])

        for sheet in sheets:
            if "charts" in sheet:
                for chart in sheet["charts"]:
                    spec = chart.get("spec", {})
                    title = spec.get("title", "").strip()
                    if title.lower() == chart_name.lower():
                        return chart["chartId"]
        return None
    except Exception as e:
        print(f"Error scanning existing charts: {e}")
        return None

# Helper to execute chart request
def execute_request(service, spreadsheet_id, request, chart_name):
    try:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [request]}
        ).execute()
        return True
    except HttpError as e:
        print(f"Failed to execute chart request '{chart_name}': {e}")
        return False
    
# Helper to split data by week
def split_data_by_week(values, x_column, y_column):
    """
    Splits sheet data into weekly chunks.
    Returns a list of tuples:
        (x_range, y_range, week_start_str, week_end_str, week_number)
    """
    data = []
    x_index = ord(x_column) - ord("A")
    y_index = ord(y_column) - ord("A")

    for idx, row in enumerate(values):
        if len(row) <= max(x_index, y_index):
            continue

        date_val = row[x_index].strip()
        y_val = row[y_index].strip()

        try:
            date_obj = datetime.strptime(date_val, "%Y-%m-%d")
            y_float = float(y_val) if y_val else None
            if y_float is not None:
                data.append((idx + 2, date_obj, y_float))  # row number in sheet
        except:
            continue

    if not data:
        return []

    # Sort chronologically
    data.sort(key=lambda x: x[1])

    # Group by ISO weeks (Monday=0)
    weeks = itertools.groupby(data, key=lambda x: x[1] - timedelta(days=x[1].weekday()))

    result = []
    week_number = 1

    for week_start_date, items in weeks:
        items = list(items)
        first_row = items[0][0]
        last_row = items[-1][0] + 1  # non-inclusive

        # x range
        x_range = {
            "sheetId": None,
            "startRowIndex": first_row - 1,
            "endRowIndex": last_row,
            "startColumnIndex": x_index,
            "endColumnIndex": x_index + 1
        }

        # y range
        y_range = {
            "sheetId": None,
            "startRowIndex": first_row - 1,
            "endRowIndex": last_row,
            "startColumnIndex": y_index,
            "endColumnIndex": y_index + 1
        }

        # Week start = Monday
        week_start = week_start_date
        # Week end = Sunday
        week_end = week_start + timedelta(days=6)

        week_start_str = week_start.strftime("%Y-%m-%d")
        week_end_str = week_end.strftime("%Y-%m-%d")

        result.append(
            (x_range, y_range, week_start_str, week_end_str, week_number)
        )

        week_number += 1

    return result
