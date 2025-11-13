# backend/app/mcp_servers/gforms_server.py

from typing import Dict, Any, List, Optional
from googleapiclient.discovery import build

from ..integrations.google_auth import get_authorized_http
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GFormsMCPServer:
    def __init__(self):
        self.service = None
        self.DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

    def _get_service(self):
        """Initializes and returns the Google Forms API service (v1)."""
        if not self.service:
            http = get_authorized_http()
            self.service = build(
                'forms', 
                'v1', 
                http=http, 
                discoveryServiceUrl=self.DISCOVERY_DOC, 
                static_discovery=False
            )
        return self.service

    # Helper to generate form requests
    def _create_question_request(self, question_text: str, question_type: str, options: Optional[List[str]] = None, index: int = 0) -> Dict[str, Any]:
        """Generates a batchUpdate request for creating a question."""
        item = {"title": question_text, "questionItem": {"question": {"required": True}}}
        
        if question_type == 'multiple_choice' and options:
            item['questionItem']['question']['choiceQuestion'] = {
                'type': 'RADIO',
                'options': [{'value': opt} for opt in options]
            }
        elif question_type == 'short_answer':
            item['questionItem']['question']['textQuestion'] = {}
        # Add more types as needed (checkbox, paragraph, etc.)

        return {
            "createItem": {
                "item": item,
                "location": {"index": index}
            }
        }

    # Tool: gforms_create_form
    def gforms_create_form(self, title: str, questions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Creates a new Google Form with a title and optional questions."""
        try:
            service = self._get_service()
            
            # 1. Create the new form
            new_form = service.forms().create(body={'info': {'title': title}}).execute()
            form_id = new_form.get('formId')
            
            # 2. Add questions if provided
            if questions:
                requests = []
                for i, q in enumerate(questions):
                    q_type = q.get('type', 'short_answer')
                    q_options = q.get('options')
                    requests.append(self._create_question_request(q['question'], q_type, q_options, i))
                
                if requests:
                    service.forms().batchUpdate(
                        formId=form_id, 
                        body={'requests': requests}
                    ).execute()

            return {
                "status": "success",
                "message": f"Google Form '{title}' created with {len(questions) if questions else 0} questions.",
                "details": {"id": form_id, "submitUrl": new_form.get('responderUri')}
            }
        
        except Exception as e:
            logger.error(f"Failed to create Google Form: {e}")
            return {"status": "error", "message": f"Failed to create Google Form. Details: {str(e)}"}

    # Tool: gforms_read_form
    def gforms_read_form(self, form_id: str) -> Dict[str, Any]:
        """Retrieves metadata and questions from a Google Form."""
        try:
            service = self._get_service()
            form = service.forms().get(formId=form_id).execute()
            
            return {
                "status": "success",
                "title": form.get('info', {}).get('title'),
                "details": {"items": [i.get('title') for i in form.get('items', []) if 'title' in i]}
            }
        
        except Exception as e:
            logger.error(f"Failed to read Google Form: {e}")
            return {"status": "error", "message": f"Failed to read Google Form. Details: {str(e)}"}

    # Tool: gforms_get_responses
    def gforms_get_responses(self, form_id: str) -> Dict[str, Any]:
        """Fetches all responses submitted to a Google Form."""
        try:
            service = self._get_service()
            responses = service.forms().responses().list(formId=form_id).execute()
            
            return {
                "status": "success",
                "message": f"Fetched {len(responses.get('responses', []))} responses.",
                "responses": responses.get('responses', [])
            }
        
        except Exception as e:
            logger.error(f"Failed to get form responses: {e}")
            return {"status": "error", "message": f"Failed to get form responses. Details: {str(e)}"}