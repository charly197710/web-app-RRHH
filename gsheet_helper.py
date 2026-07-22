import os
import csv
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Path to service account JSON (set via env var GSHEETS_SA_PATH or default)
SERVICE_ACCOUNT_FILE = os.getenv(
    "GSHEETS_SA_PATH",
    os.path.join(os.path.expanduser("~"), "google-credentials", "hr-recruitment-sa.json")
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

def _get_client():
    if not os.path.isfile(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

def _get_drive_service():
    if not os.path.isfile(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds, cache_discovery=False)

def write_dataframe_to_sheet(rows: list, spreadsheet_title: str, worksheet_name: str = "Hoja1") -> str:
    """
    rows: list of lists, where first inner list is header.
    Creates (if not exists) a spreadsheet with given title and writes rows into worksheet_name.
    Returns the spreadsheet URL.
    """
    client = _get_client()
    try:
        sh = client.open(spreadsheet_title)
    except gspread.SpreadsheetNotFound:
        sh = client.create(spreadsheet_title)
    # Ensure worksheet exists
    try:
        ws = sh.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=worksheet_name, rows=str(max(len(rows) + 10, 100)), cols=str(max(len(rows[0]) if rows else 10) + 10, 20))
    # Clear existing content
    ws.clear()
    # Update the whole sheet
    ws.update('A1', rows)
    return sh.url

def share_spreadsheet(spreadsheet_url: str, email: str, role: str = "writer"):
    """
    Grants permission to email on the spreadsheet identified by URL.
    role: 'reader', 'writer', 'commenter'
    """
    # Extract spreadsheet ID from URL
    # Format: https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit
    try:
        parts = spreadsheet_url.split('/d/')
        if len(parts) != 2:
            raise ValueError("Unable to parse spreadsheet ID from URL")
        spreadsheet_id = parts[1].split('/')[0]
    except Exception as e:
        raise ValueError(f"Invalid spreadsheet URL: {spreadsheet_url}") from e

    drive_service = _get_drive_service()
    permission_body = {
        'type': 'user',
        'role': role,
        'emailAddress': email
    }
    drive_service.permissions().create(
        fileId=spreadsheet_id,
        body=permission_body,
        fields='id'
    ).execute()
