import os
import shutil
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.qparser import QueryParser
from sqlalchemy.orm import Session
from ..models.resource import Resource
from ..config import UPLOAD_PATH

INDEX_DIR = os.path.join(UPLOAD_PATH, 'whoosh_index')


class SearchService:
    def __init__(self):
        self.schema = Schema(
            id=ID(stored=True),
            user_id=ID(stored=True),
            filename=TEXT(stored=True),
            content=TEXT(stored=True)
        )
        self._ensure_index_dir()
    
    def _ensure_index_dir(self):
        os.makedirs(INDEX_DIR, exist_ok=True)
    
    def create_or_open_index(self):
        if os.path.exists(os.path.join(INDEX_DIR, '_MAIN_')):
            return open_dir(INDEX_DIR)
        return create_in(INDEX_DIR, self.schema)
    
    def add_document(self, user_id: int, resource_id: int, filename: str, content: str):
        ix = self.create_or_open_index()
        writer = ix.writer()
        writer.add_document(
            id=str(resource_id),
            user_id=str(user_id),
            filename=filename,
            content=content
        )
        writer.commit()
    
    def update_document(self, user_id: int, resource_id: int, filename: str, content: str):
        ix = self.create_or_open_index()
        writer = ix.writer()
        writer.update_document(
            id=str(resource_id),
            user_id=str(user_id),
            filename=filename,
            content=content
        )
        writer.commit()
    
    def delete_document(self, resource_id: int):
        ix = self.create_or_open_index()
        writer = ix.writer()
        writer.delete_by_term('id', str(resource_id))
        writer.commit()
    
    def search(self, user_id: int, query_str: str, limit: int = 10) -> list:
        try:
            ix = self.create_or_open_index()
            with ix.searcher() as searcher:
                parser = QueryParser('content', ix.schema)
                query = parser.parse(query_str)
                results = searcher.search(query, limit=limit)
                
                matched_ids = set()
                for result in results:
                    if result['user_id'] == str(user_id):
                        matched_ids.add(int(result['id']))
                
                return list(matched_ids)
        except Exception:
            return []
    
    def rebuild_index(self, db: Session, user_id: int = None):
        ix = self.create_or_open_index()
        writer = ix.writer()
        writer.mergetype = 'clear'
        
        if user_id:
            resources = db.query(Resource).filter(Resource.user_id == user_id).all()
        else:
            resources = db.query(Resource).all()
        
        for resource in resources:
            content = self._extract_text(resource.storage_path)
            writer.add_document(
                id=str(resource.id),
                user_id=str(resource.user_id),
                filename=resource.filename,
                content=content
            )
        
        writer.commit()
    
    def _extract_text(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return ""
        
        ext = file_path.split('.')[-1].lower()
        
        try:
            if ext == 'pdf':
                return self._extract_pdf(file_path)
            elif ext in ['doc', 'docx']:
                return self._extract_docx(file_path)
            elif ext == 'txt':
                return self._extract_txt(file_path)
            elif ext == 'md':
                return self._extract_txt(file_path)
            else:
                return ""
        except Exception:
            return ""
    
    def _extract_pdf(self, file_path: str) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            return ""
    
    def _extract_docx(self, file_path: str) -> str:
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except ImportError:
            return ""
    
    def _extract_txt(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return ""


search_service = SearchService()