import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from gspread.utils import rowcol_to_a1


# Helper class to handle Google Sheets authentication and access
class GoogleSheetAuth:
    def __init__(self, cred_file: str, sheet_name: str):
        self.cred_file = cred_file
        self.sheet_name = sheet_name

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        self.creds = Credentials.from_service_account_file(cred_file, scopes=scopes)
        self.client = gspread.authorize(self.creds)
        self.spreadsheet = self.client.open(sheet_name)

        # **Add this service object for Sheets API calls**
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.spreadsheet_id = self.spreadsheet.id
    # Get a specific sheet by name or the first sheet by default
    def get_sheet(self, sheet_name=None):
        if sheet_name:
            return self.spreadsheet.worksheet(sheet_name)
        return self.spreadsheet.sheet1
    # Add a new sheet with the given name
    def add_sheet(self, sheet_name: str):
        try:
            sheet = self.spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            sheet = self.spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")
        return sheet

 