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

    def parse_file(self, file_path: str, progress_callback=None) -> str:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self._parse_pdf(file_path, progress_callback)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            return self._parse_image(file_path)
        elif file_ext in ['.doc', '.docx']:
            return self._parse_docx(file_path)
        elif file_ext == '.txt':
            return self._parse_txt(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")

    def _parse_pdf(self, file_path: str, progress_callback=None) -> str:
        try:
            text = self._parse_pdf_with_fitz(file_path, progress_callback)
            
            if text and len(text.strip()) > 100:
                chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
                if chinese_count > len(text) * 0.1:
                    return self._clean_text(text)
            
            pymupdf_text = text
            
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            pypdf_text = ""
            has_text = False
            
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    has_text = True
                    pypdf_text += page_text + "\n\n"
                
                if progress_callback and total_pages > 0:
                    page_progress = int(5 + (i + 1) / total_pages * 15)
                    if page_progress % 5 == 0 or i == total_pages - 1:
                        progress_callback(page_progress, f"正在解析第 {i + 1}/{total_pages} 页...")
            
            if has_text and len(pypdf_text.strip()) > 100:
                pypdf_chinese = sum(1 for c in pypdf_text if '\u4e00' <= c <= '\u9fff')
                if pymupdf_text and pypdf_chinese < chinese_count * 0.5:
                    return self._clean_text(pymupdf_text)
                return self._clean_text(pypdf_text)
            
            if pymupdf_text and len(pymupdf_text.strip()) > 100:
                return self._clean_text(pymupdf_text)
            
            if progress_callback:
                progress_callback(10, "检测为扫描版PDF，开始OCR识别...")
            
            return self._parse_scanned_pdf(file_path, progress_callback)
        except Exception:
            if progress_callback:
                progress_callback(5, "PDF解析失败，尝试OCR识别...")
            return self._parse_scanned_pdf(file_path, progress_callback)

    def _parse_pdf_with_fitz(self, file_path: str, progress_callback=None) -> str:
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            text = ""
            
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                if page_text and page_text.strip():
                    text += page_text + "\n\n"
                
                if progress_callback and total_pages > 0:
                    page_progress = int(5 + (page_num + 1) / total_pages * 15)
                    if page_progress % 5 == 0 or page_num == total_pages - 1:
                        progress_callback(page_progress, f"正在解析第 {page_num + 1}/{total_pages} 页...")
            
            doc.close()
            return text
        except Exception:
            return ""

    def _parse_scanned_pdf(self, file_path: str, progress_callback=None) -> str:
        text = ""
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            
            for page_num, page in enumerate(doc):
                pix = page.get_pixmap()
                temp_image = f"temp_page_{page_num}.png"
                pix.save(temp_image)
                page_text = self._parse_image(temp_image)
                text += page_text + "\n\n"
                if os.path.exists(temp_image):
                    os.remove(temp_image)
                
                if progress_callback:
                    ocr_progress = int(10 + (page_num + 1) / total_pages * 10)
                    progress_callback(ocr_progress, f"OCR识别中... 第 {page_num + 1}/{total_pages} 页")
            
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
                if cleaned_lines and cleaned_lines[-1] != '':
                    cleaned_lines.append('')
                continue
            
            if self._is_invalid_line(line):
                continue
            
            cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

    def _is_invalid_line(self, line: str) -> bool:
        if len(line) <= 1:
            return True
        
        if re.match(r'^[\s\W]{3,}$', line):
            return True
        
        if re.match(r'^[\d]{8,}$', line):
            return True
        
        if re.match(r'^[a-zA-Z]{15,}$', line):
            return True
        
        invalid_keywords = ['undefined', 'null', 'NaN', 'error', 'failed']
        line_lower = line.lower()
        for kw in invalid_keywords:
            if kw in line_lower:
                return True
        
        char_count = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
        eng_count = sum(1 for c in line if c.isalpha())
        num_count = sum(1 for c in line if c.isdigit())
        math_symbols = sum(1 for c in line if c in '=+-*/()[]{}|<>^_∫∑∏√∞≈≠≤≥∈∉⊂⊃∪∩')
        total = len(line)
        
        if total > 0 and char_count == 0 and eng_count == 0 and math_symbols == 0:
            return True
        
        if total >= 8 and char_count == 0 and math_symbols == 0 and num_count >= total * 0.9:
            return True
        
        return False


ocr_parser = OCRParser()
