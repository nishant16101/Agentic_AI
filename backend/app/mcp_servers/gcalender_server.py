from typing import Dict, Any, List, Optional
from googleapiclient.discovery import build
from datetime import datetime,timedelta

from ..integrations.google_auth import get_authorized_http
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GCalendarMCPServer:
    def __init__(self):
        self.service = None
        self.calendar_id = 'primary' 
    
    def _get_service(self):
        if not self.service:
            http = get_authorized_http()
            self.service = build('calendar', 'v3', http=http)
        return self.service
    
    #tool: calendar schedule meeting
    def calendar_schedule_meeting(self,summary:str,attendees:List[str],start_time:str,end_time:Optional[str]=None,location:Optional[str] = None)->Dict[str,Any]:
        try:
            service = self._get_service()
            start_dt = datetime.fromisoformat(start_time)
            end_time = datetime.fromisoformat(end_time) if end_time else (start_dt+timedelta(hours=1))
            
            event = {
                'summary': summary,
                'location': location,
                'attendees': [{'email': email} for email in attendees],
                'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'UTC'},
                'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'},
                # Request a Meet link automatically
                'conferenceData': {'createRequest': {'requestId': f"meet-{datetime.now().timestamp()}", 'conferenceSolutionKey': {'type': 'hangoutsMeet'}}},
            }

            created_event = service.events().insert(
                calendarId = self.calendar_id,
                body = event,
                conferenceDataVersion=1
            ).execute()
            return{
                "status":"success",
                "message":f"Meeting{summary} scheduled successfully.",
                "details": {"id": created_event.get('id'), "link": created_event.get('htmlLink')}
            }
        except Exception as e:
                logger.error(f"Failed to schedule meeting: {e}")
                return {"status": "error", "message": f"Failed to schedule meeting. Details: {str(e)}"}

        
    def calendar_cancel_event(self, event_id: str) -> Dict[str, Any]:
        """Cancels an existing calendar event."""
        try:
            service = self._get_service()
            service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
            
            return {
                "status": "success",
                "message": f"Event with ID {event_id} cancelled successfully."
            }
        except Exception as e:
            logger.error(f"Failed to cancel event: {e}")
            return {"status": "error", "message": f"Failed to cancel event. Details: {str(e)}"}
        
    #tool:calendr list events
    def calendar_list_events(self,time_min:Optional[str]=None,time_max:Optional[str]=None,max_results:int=10)->Dict[str,Any]:
        """List upcoming events"""
        try:
            service = self._get_service()   
            if not time_min:
                time_min = datetime.now().isoformat() + 'Z' 

            events_result = service.events().List(
                calendarId=self.calendar_id,
                timeMin = time_min,
                timeMax = time_max,
                maxResults = max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            event_summaries = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                event_summaries.append({
                    "id": event['id'],
                    "summary": event.get('summary', 'No Title'),
                    "start": start,
                    "location": event.get('location', 'N/A')
                })
            return {
                "status": "success",
                "message": f"Found {len(event_summaries)} upcoming event(s).",
                "events": event_summaries
            }
        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            return {"status": "error", "message": f"Failed to list events. Details: {str(e)}"}
