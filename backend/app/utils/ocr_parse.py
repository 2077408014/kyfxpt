import os
import re
from typing import Optional
from rapidocr_onnxruntime import RapidOCR
from PyPDF2 import PdfReader
from docx import Document
import fitz


class OCRParser:
    def __init__(self):
        self.ocr_engine = RapidOCR()

    def parse_file(self, file_path: str) -> str:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self._parse_pdf(file_path)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            return self._parse_image(file_path)
        elif file_ext in ['.doc', '.docx']:
            return self._parse_docx(file_path)
        elif file_ext == '.txt':
            return self._parse_txt(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")

    def _parse_pdf(self, file_path: str) -> str:
        try:
            reader = PdfReader(file_path)
            text = ""
            has_text = False
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    has_text = True
                    text += page_text + "\n\n"
            
            if has_text and len(text.strip()) > 100:
                return self._clean_text(text)
            
            return self._parse_scanned_pdf(file_path)
        except Exception:
            return self._parse_scanned_pdf(file_path)

    def _parse_scanned_pdf(self, file_path: str) -> str:
        text = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                pix = page.get_pixmap()
                temp_image = f"temp_page_{page.number}.png"
                pix.save(temp_image)
                page_text = self._parse_image(temp_image)
                text += page_text + "\n\n"
                if os.path.exists(temp_image):
                    os.remove(temp_image)
            return self._clean_text(text)
        except Exception as e:
            return ""

    def _parse_image(self, file_path: str) -> str:
        try:
            result, _ = self.ocr_engine(file_path)
            if not result:
                return ""
            
            filtered_results = []
            for item in result:
                if len(item) >= 3 and item[2] > 0.55:
                    filtered_results.append(item)
            
            filtered_results.sort(key=lambda x: (x[0][0][1], x[0][0][0]))
            
            texts = []
            for item in filtered_results:
                texts.append(item[1])
            
            raw_text = "\n".join(texts)
            return self._clean_text(raw_text)
        except Exception:
            return ""

    def _parse_docx(self, file_path: str) -> str:
        try:
            doc = Document(file_path)
            text = ""
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n\n"
            return self._clean_text(text)
        except Exception:
            return ""

    def _parse_txt(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            return self._clean_text(text)
        except Exception:
            try:
                with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                    text = f.read()
                return self._clean_text(text)
            except Exception:
                return ""

    def _clean_text(self, text: str) -> str:
        text = text.replace('\r\n', '\n')
        text = text.replace('\u3000', ' ')
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if self._is_invalid_line(line):
                continue
            
            cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'\s{2,}', ' ', text)
        
        return text.strip()

    def _is_invalid_line(self, line: str) -> bool:
        if len(line) <= 1:
            return True
        
        invalid_patterns = [
            r'^[\s\W]{3,}$',
            r'^[><=\-\+\*/\|\(\)\[\]{}]{2,}$',
            r'^[\d]{8,}$',
            r'^[a-zA-Z]{12,}$',
            r'^[^\w\u4e00-\u9fff]{4,}$',
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, line):
                return True
        
        invalid_keywords = ['undefined', 'null', 'NaN', 'error', 'failed']
        line_lower = line.lower()
        for kw in invalid_keywords:
            if kw in line_lower:
                return True
        
        char_count = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
        eng_count = sum(1 for c in line if c.isalpha())
        num_count = sum(1 for c in line if c.isdigit())
        total = len(line)
        
        if total > 0 and char_count == 0 and eng_count == 0:
            return True
        
        if total >= 5 and char_count == 0 and num_count >= total * 0.8:
            return True
        
        return False


ocr_parser = OCRParser()
