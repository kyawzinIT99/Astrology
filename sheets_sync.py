"""
Google Sheets Sync for Tarot Bookings — Service Account Auth.

Uses a Google Service Account for direct Sheet access.
No OAuth consent flow needed. Just share the Sheet with the
service account email: n8n-kz@learningn8n-472912.iam.gserviceaccount.com
"""

import os
import gspread
from google.oauth2.service_account import Credentials

# Configuration
SPREADSHEET_ID = "16bdB_0wtpYYACVQ_bDFBVYml8xpG2GYam9IuN6SylsM"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")

# Sheet headers — only essential booking info
HEADERS = ["booking_id", "name", "phone", "dob", "date", "time", "status"]


def get_client():
    """Get an authorized gspread client using service account."""
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def get_sheet():
    """Get the 'Bookings' worksheet, creating it if needed."""
    try:
        client = get_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)

        try:
            worksheet = spreadsheet.worksheet("Bookings")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet("Bookings", rows=200, cols=len(HEADERS))
            worksheet.update("A1", [HEADERS])
            worksheet.format("A1:G1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.35, "green": 0.11, "blue": 0.53}
            })

        return worksheet

    except Exception as e:
        print(f"⚠️ Google Sheets connection error: {e}")
        return None


def sync_new_booking(booking: dict) -> bool:
    """Append a single new booking row to Google Sheets."""
    try:
        worksheet = get_sheet()
        if not worksheet:
            return False

        row = [booking.get(h, "") for h in HEADERS]
        worksheet.append_row(row, value_input_option="RAW")
        print(f"✅ Booking {booking.get('booking_id', '?')} synced to Google Sheets")
        return True

    except Exception as e:
        print(f"⚠️ Google Sheets sync error: {e}")
        return False


def sync_status_update(booking: dict, new_status: str) -> bool:
    """
    Update a booking's status in Google Sheets.
    Finds the row by booking_id and updates the status column.
    """
    try:
        worksheet = get_sheet()
        if not worksheet:
            return False

        # Find the booking row by booking_id (column A)
        booking_id = booking.get("booking_id", "")
        cell = worksheet.find(booking_id)
        if cell:
            # Status is column G (index 7)
            worksheet.update_cell(cell.row, 7, new_status)
            print(f"✅ Booking {booking_id} status → {new_status} in Google Sheets")
            return True
        else:
            print(f"⚠️ Booking {booking_id} not found in Sheet, appending...")
            booking_copy = dict(booking)
            booking_copy["status"] = new_status
            return sync_new_booking(booking_copy)

    except Exception as e:
        print(f"⚠️ Google Sheets status update error: {e}")
        return False


def sync_all_bookings(bookings: list) -> bool:
    """Full sync: overwrite all bookings in the sheet."""
    try:
        worksheet = get_sheet()
        if not worksheet:
            return False

        worksheet.clear()
        worksheet.update("A1", [HEADERS])

        rows = [[b.get(h, "") for h in HEADERS] for b in bookings]
        if rows:
            worksheet.update(f"A2:G{len(rows)+1}", rows)

        print(f"✅ {len(rows)} bookings synced to Google Sheets")
        return True

    except Exception as e:
        print(f"⚠️ Google Sheets full sync error: {e}")
        return False


def is_connected() -> bool:
    """Quick check if service account can access the sheet."""
    try:
        ws = get_sheet()
        return ws is not None
    except Exception:
        return False


if __name__ == "__main__":
    print("🔗 Testing Google Sheets Service Account connection...")
    if is_connected():
        ws = get_sheet()
        print(f"✅ Connected to worksheet: {ws.title}")
        records = ws.get_all_records()
        print(f"   Found {len(records)} existing rows")
    else:
        print("❌ Cannot connect. Check credentials.json and sheet sharing.")
        print(f"   Share the sheet with: n8n-kz@learningn8n-472912.iam.gserviceaccount.com")
