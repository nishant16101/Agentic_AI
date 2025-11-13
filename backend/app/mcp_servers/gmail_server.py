from typing import Dict, Any
from googleapiclient.discovery import build
from email.mine.text import MIMEText
import base64

from ..integrations.google_auth import get_authorized_http
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GmailMCPServer:
    def __init__(self):
        self.service = None

    def _get_service(self):
        if not self.service:
            http = get_authorized_http()
            self.service = build('gmail', 'v1', http=http)
        return self.service
    
    def send_email(self,recipient:str,subject:str,body:str)->Dict[str,Any]:
        """Sends an email using Gmail Api"""
        try:
            service = self._get_service()
            message = MIMEText(body)
            message['to'] = recipient
            message['subject'] = subject

            #encode the message for api
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode(  )

            #send message
            sent_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}).execute()
            
            logger.info(f"Email sent to {recipient} with id {sent_message['id']}")

            return {
                "status": "success",
                "message": f"Email to {recipient} with subject '{subject}' has been sent.",
                "details": {"id": sent_message.get('id'), "threadId": sent_message.get('threadId')}
            }
        except Exception as e:
            logger.error(f"Failed to send email:{e}")
            return {
                "status": "error",
                "message": f"Failed to send email: {e}"
            }
    # Tool: gmail_delete_email
    def gmail_delete_email(self, message_id: str) -> Dict[str, Any]:
        """Deletes an email."""
        try:
            service = self._get_service()
            service.users().messages().delete(userId='me', id=message_id).execute()
            
            return {
                "status": "success",
                "message": f"Email with ID {message_id} deleted successfully."
            }
        except Exception as e:
            logger.error(f"Failed to delete email: {e}")
            return {"status": "error", "message": f"Failed to delete email. Details: {str(e)}"}

    # Tool: gmail_read_emails
    def gmail_read_emails(self, max_results: int = 5, query: Optional[str] = None) -> Dict[str, Any]:
        """Reads recent emails."""
        try:
            service = self._get_service()
            
            response = service.users().messages().list(
                userId='me', 
                maxResults=max_results, 
                q=query
            ).execute()
            
            messages = response.get('messages', [])
            email_summaries = []
            
            if messages:
                for msg in messages:
                    # Fetching full message for subject/snippet (can be slow for many messages)
                    full_msg = service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject', 'From']).execute()
                    
                    snippet = full_msg.get('snippet', 'No snippet available.')
                    headers = {h['name']: h['value'] for h in full_msg.get('payload', {}).get('headers', [])}

                    email_summaries.append({
                        "id": msg['id'],
                        "from": headers.get('From', 'Unknown Sender'),
                        "subject": headers.get('Subject', 'No Subject'),
                        "snippet": snippet
                    })

            return {
                "status": "success",
                "message": f"Found {len(email_summaries)} email(s).",
                "emails": email_summaries
            }
        
        except Exception as e:
            logger.error(f"Failed to read emails: {e}")
            return {"status": "error", "message": f"Failed to read emails. Details: {str(e)}"}