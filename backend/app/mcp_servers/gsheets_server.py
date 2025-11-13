

from typing import Dict, Any, List
from googleapiclient.discovery import build

from ..integrations.google_auth import get_authorized_http
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GSheetsMCPServer:
    def __init__(self):
        self.service = None

    def _get_service(self):
        """Initializes and returns the Google Sheets API service (v4)."""
        if not self.service:
            http = get_authorized_http()
            self.service = build('sheets', 'v4', http=http)
        return self.service

    # Tool: gsheet_create_sheet
    def gsheet_create_sheet(self, title: str) -> Dict[str, Any]:
        """Creates a new Google Spreadsheet."""
        try:
            service = self._get_service()
            
            spreadsheet_body = {'properties': {'title': title}}
            spreadsheet = service.spreadsheets().create(
                body=spreadsheet_body, 
                fields='spreadsheetId,spreadsheetUrl'
            ).execute()
            
            return {
                "status": "success",
                "message": f"Spreadsheet '{title}' created.",
                "details": {"id": spreadsheet.get('spreadsheetId'), "url": spreadsheet.get('spreadsheetUrl')}
            }
        
        except Exception as e:
            logger.error(f"Failed to create Google Sheet: {e}")
            return {"status": "error", "message": f"Failed to create Google Sheet. Details: {str(e)}"}

    # Tool: gsheet_read_sheet
    def gsheet_read_sheet(self, spreadsheet_id: str, range: str) -> Dict[str, Any]:
        """Reads data from a specified range."""
        try:
            service = self._get_service()
            
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, 
                range=range
            ).execute()
            
            values = result.get('values', [])
            
            return {
                "status": "success",
                "message": f"Read {len(values)} rows from range {range}.",
                "values": values
            }
        
        except Exception as e:
            logger.error(f"Failed to read sheet data: {e}")
            return {"status": "error", "message": f"Failed to read sheet data. Details: {str(e)}"}

    # Tool: gsheet_update_sheet
    def gsheet_update_sheet(self, spreadsheet_id: str, range: str, values: List[List[str]]) -> Dict[str, Any]:
        """Writes or updates data in a specified range."""
        try:
            service = self._get_service()
            
            body = {'values': values}
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, 
                range=range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            return {
                "status": "success",
                "message": f"Updated {result.get('updatedCells')} cells in the sheet.",
                "details": {"updatedRange": result.get('updatedRange')}
            }
        
        except Exception as e:
            logger.error(f"Failed to update sheet data: {e}")
            return {"status": "error", "message": f"Failed to update sheet data. Details: {str(e)}"}