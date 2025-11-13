from typing import Dict,Any,Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..integrations.google_auth import get_authorized_http
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GDocsMCPServer:
    def __init__(self):
        self.docs_service = None

    def _get_service(self):
        """Initializes and returns the Google Docs service."""
        if not self.docs_service:
            http = get_authorized_http()
            self.docs_service = build('docs', 'v1', http=http)
        return self.docs_service
    
    def gdocs_create_document(self,title:str,content:Optional[str]=None)->Dict[str,Any]:
        """Creates a new Google Doc and optionally inserts initial content."""
        try:
            service = self._get_service()
            document = service.documents().create(body={'title': title}).execute()
            document_id = document.get('documentId')

            if content:
                requests = [{'insertText': {'text': content, 'endIndex': 1}}]
                service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()

            return {
                "status": "success",
                "message": f"Document '{title}' created.",
                "details": {"id": document_id, "link": document.get('webViewLink')}
            }
        
        except Exception as e:
            logger.erro(f"Failed to create document: {e}")
            return {"status": "error", "message": f"Failed to create document. Details: {str(e)}"}
        

    def gdocs_read_document(self,document_id:str)->Dict[str,Any]:
        """Retrives the text content of a Google Doc"""
        try:
            service = self._get_service()
            document = service.documents().get(documentId = document_id).execute()

            content_text = ""
            for element in document.get('body',{}).get('content',[]):
                if 'paragraph' in element:
                    for run in element['paragraph']['element']:
                        if 'textRun' in run:
                            content_text += run['textRun']['content']
            return {
                "status": "success",
                "title": document.get('title'),
                "content": content_text.strip()
            }
        except HttpError as e:
            logger.error(f"Error reading document:{e}")
            return {"status": "error", "message": f"Failed to read document. Details: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error reading document:{e}")
            return {"status": "error", "message": f"Failed to read document. Details: {str(e)}"}
        
    # Tool: gdocs_update_document
    def gdocs_update_document(self, document_id: str, content: str) -> Dict[str, Any]:
        """Updates the content of a Google Doc (appends to the end)."""
        try:
            service = self._get_service()
            
            # Find the end of the document
            document = service.documents().get(documentId=document_id, fields='body.content').execute()
            end_index = document['body']['content'][-1]['endIndex'] - 1
            
            requests = [
                {
                    'insertText': {
                        'text': content,
                        'endIndex': end_index,
                    }
                }
            ]
            service.documents().batchUpdate(
                documentId=document_id, 
                body={'requests': requests}
            ).execute()
            
            return {
                "status": "success",
                "message": f"Content appended to document ID {document_id}."
            }
        
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            return {"status": "error", "message": f"Failed to update document. Details: {str(e)}"}
