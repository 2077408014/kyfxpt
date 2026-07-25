from typing import Optional, Tuple, List, Dict
import threading
import os
import hashlib
import time

SUBJECT_KEYWORDS = {
    "数学": ["极限", "导数", "微分", "积分", "级数", "矩阵", "行列式",
            "向量", "概率", "随机变量", "方程", "不等式", "数列",
            "函数", "泰勒", "拉格朗日", "柯西", "偏导", "线性方程组",
            "特征值", "特征向量", "二次型", "分布", "期望", "方差"],
    "英语": ["reading", "passage", "vocabulary", "grammar", "translation",
            "cloze", "essay", "writing", "verb", "noun", "adjective",
            "sentence", "paragraph", "comprehension", "blank"],
    "政治": ["马克思", "唯物", "辩证", "毛泽东", "中国特色社会主义",
            "政治经济学", "哲学", "价值观", "矛盾", "实践", "认识论",
            "剩余价值", "资本", "共产主义", "改革开放", "社会主义"],
}

KNOWLEDGE_POINTS = {
    "数学": {
        "高等数学-极限": ["极限", "收敛", "发散", "洛必达"],
        "高等数学-导数": ["导数", "微分", "偏导", "链式法则"],
        "高等数学-积分": ["积分", "定积分", "不定积分", "换元"],
        "线性代数": ["矩阵", "行列式", "特征值", "特征向量", "线性方程组"],
        "概率统计": ["概率", "分布", "期望", "方差", "随机变量"],
    },
    "英语": {
        "阅读理解": ["passage", "reading", "main idea", "author"],
        "完形填空": ["cloze", "blank", "fill"],
        "翻译": ["translate", "translation"],
        "写作": ["writing", "essay", "letter"],
    },
    "政治": {
        "马克思主义原理": ["马克思", "唯物", "辩证", "哲学"],
        "毛中特": ["毛泽东", "中国特色社会主义", "改革开放"],
        "政治经济学": ["剩余价值", "资本", "商品"],
    },
}

INVALID_PATTERNS = [
    r'^[\s\W]{3,}$',
    r'^[><=\-\+\*/\|\(\)\[\]{}]{2,}$',
    r'^[\d]{5,}$',
    r'^[a-zA-Z]{10,}$',
    r'^[^\w\u4e00-\u9fff]{4,}$',
    r'^[`~!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{3,}$',
]

INVALID_KEYWORDS = [
    'undefined', 'null', 'NaN', 'error', 'failed', 'loading', 'list',
    'http://', 'https://', '.com', '.cn', '.org', '.net',
    'www.', 'mailto:', 'tel:', 'javascript:', 'function',
    'class', 'import', 'export', 'const', 'let', 'var',
    'console.', 'alert(', 'debugger', 'return', 'if(', 'for(', 'while('
]

PUNCTUATION_END = ['。', '；', '！', '？', '.', ';', '!', '?', ':', '：']
PUNCTUATION_CONTINUE = [',', '，', '、', '—', '-', '…', '.', '·']
NUMBER_PREFIX = ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '0.',
                 '①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩',
                 '一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、', '九、', '十、',
                 '（1）', '（2）', '（3）', '（4）', '（5）',
                 '(1)', '(2)', '(3)', '(4)', '(5)',
                 '1)', '2)', '3)', '4)', '5)',
                 '【', '[', '(']

HEADING_KEYWORDS = ['第一节', '第二节', '第三节', '第四节', '第五节',
                    '第一章', '第二章', '第三章', '第四章', '第五章',
                    '一、', '二、', '三、', '四、', '五、',
                    '1.', '2.', '3.', '4.', '5.',
                    '（一）', '（二）', '（三）', '（四）', '（五）',
                    '(一)', '(二)', '(三)', '(四)', '(五)']

EMPHASIS_PATTERNS = [
    (r'【([^】]+)】', r'◆ \1'),
    (r'\[([^\]]+)\]', r'◇ \1'),
    (r'「([^」]+)」', r'▶ \1'),
    (r'《([^》]+)》', r'★ 《\1》'),
]

KEY_CONCEPTS = [
    '【背', '【选择题', '【简答题', '【辨析题', '【新增',
    '口诀', '注意', '重点', '核心', '关键',
    '决定', '制约', '作用', '功能', '影响',
    '特征', '规律', '原则', '方法', '理论',
]

LIST_INDICATORS = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩',
                   '⑴', '⑵', '⑶', '⑷', '⑸',
                   '①', '②', '③', '④', '⑤',
                   '（1）', '（2）', '（3）', '（4）', '（5）',
                   '(1)', '(2)', '(3)', '(4)', '(5)',
                   '1)', '2)', '3)', '4)', '5)']

class OCRService:
    def __init__(self):
        self._engine = None
        self._lock = threading.Lock()
        self._cache: Dict[str, dict] = {}
        self._cache_timeout = 300

    @property
    def engine(self):
        if self._engine is None:
            with self._lock:
                if self._engine is None:
                    from rapidocr_onnxruntime import RapidOCR
                    self._engine = RapidOCR()
        return self._engine
    
    def reset_engine(self):
        with self._lock:
            self._engine = None
    
    def _clean_cache(self):
        now = time.time()
        to_remove = [key for key, value in self._cache.items() if now - value['timestamp'] > self._cache_timeout]
        for key in to_remove:
            del self._cache[key]

    def _get_cache_key(self, image_path: str) -> str:
        file_stat = os.stat(image_path)
        return hashlib.md5(f"{image_path}_{file_stat.st_mtime}_{file_stat.st_size}".encode()).hexdigest()

    def _is_invalid_line(self, line: str) -> bool:
        line = line.strip()
        if not line:
            return True
        
        if len(line) <= 1:
            return True
        
        import re
        for pattern in INVALID_PATTERNS:
            if re.match(pattern, line):
                return True
        
        line_lower = line.lower()
        for kw in INVALID_KEYWORDS:
            if kw in line_lower:
                return True
        
        char_count = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
        eng_count = sum(1 for c in line if c.isalpha())
        num_count = sum(1 for c in line if c.isdigit())
        total = len(line)
        
        math_symbols = '→←≠≤≥±∓∪∩∈∉⊂⊃⊆⊇∪∩∀∃∄∞∅∆∇∂∑∏∫∬∭∮∯∰∇√∛∜∝∞∟∠∡∢∣∥⊥⌒∂∆∇∈∉⊂⊃⊆⊇∩∪∧∨¬⇒⇔↔↕↖↗↘↙↔↕≤≥≠≈≡⊕⊗⊙⊘⊛⊠⊡⊢⊣⊤⊥⊦⊧⊨⊩⊪⊫⊬⊭⊮⊯⊰⊱⊲⊳⊴⊵⊶⊷⊸⊹⊺⊻⊼⊽⊾⊿⋀⋁⋂⋃⋄⋅⋆⋇⋈⋉⋊⋋⋌⋍⋎⋏⋐⋑⋒⋓⋔⋕⋖⋗⋘⋙⋚⋛⋜⋝⋞⋟⋠⋡⋢⋣⋤⋥⋦⋧⋨⋩⋪⋫⋬⋭⋮⋯⋰⋱→←↔↑↓↕↖↗↘↙⇀↼⇁↽⇂⇃⇄⇅⇆⇇⇈⇉⇊⇋⇌⇍⇎⇏⇐⇑⇒⇓⇔⇕⇖⇗⇘⇙⇚⇛⇜⇝⇞⇟⇠⇡⇢⇣⇤⇥⇦⇧⇨⇩⇪⇫⇬⇭⇮⇯⇰⇱⇲⇳⇴⇵⇶⇷⇸⇹⇺⇻⇼⇽⇾⇿∀∃∄∅∈∉⊂⊃⊆⊇∩∪∧∨¬⊕⊗⊙⊘⊛⊠⊡⊢⊣⊤⊥⊦⊧⊨⊩⊪⊫⊬⊭⊮⊯⊰⊱⊲⊳⊴⊵⊶⊷⊸⊹⊺⊻⊼⊽⊾⊿⅀⅁⅂⅃⅄ⅅⅆⅇⅈⅉ⅊⅋⅌⅍ⅎ⅏↕↔↖↗↘↙↕↔≤≥≠≈≡⊕⊗⊙⊘⊛⊠⊡∑∏∫∬∭∮∯∰∇√∛∜∞∟∠∡∢∣∥⊥⌒∂∆∇'
        math_count = sum(1 for c in line if c in math_symbols)
        
        has_special_chars = any(c in line for c in ['→', '∞', '∑', '∏', '∫', '√', '²', '³', '∂', '∆', '∇', '∈', '∩', '∪', '≠', '≤', '≥', '≈', '≡', '→', '←', '↔', '∀', '∃', '∅'])
        
        if total > 0 and char_count == 0 and eng_count == 0:
            if math_count > 0 or has_special_chars:
                return False
            return True
        
        if total >= 5 and char_count == 0 and num_count >= total * 0.8:
            if math_count > 0 or has_special_chars:
                return False
            return True
        
        return False

    def _is_new_paragraph(self, current_line: str, prev_line: str) -> bool:
        if not prev_line:
            return True
        
        prev_line = prev_line.strip()
        current_line = current_line.strip()
        
        if prev_line.endswith(tuple(PUNCTUATION_END)):
            return True
        
        for prefix in NUMBER_PREFIX:
            if current_line.startswith(prefix):
                return True
        
        if len(current_line) >= 15 and not prev_line.endswith(tuple(PUNCTUATION_CONTINUE)):
            return True
        
        if len(current_line) >= 30:
            return True
        
        return False

    def _is_heading(self, line: str) -> bool:
        line = line.strip()
        if not line:
            return False
        
        import re
        if re.match(r'^第[一二三四五六七八九十]+[章节节]', line):
            return True
        
        if re.match(r'^第[一二三四五六七八九十]+[、\.）)]', line):
            return True
        
        if re.match(r'^[\d]+[\.\uff0e][\s]*[\u4e00-\u9fff]{2,}', line):
            rest = line.split('.', 1)[1].strip()
            if len(rest) <= 40:
                return True
        
        if re.match(r'^[一二三四五六七八九十]+[、]', line):
            rest = line[2:].strip()
            if len(rest) <= 40:
                return True
        
        for kw in HEADING_KEYWORDS:
            if line.startswith(kw):
                rest = line[len(kw):].strip()
                if rest and len(rest) <= 50:
                    return True
        
        if len(line) <= 30 and line.isupper():
            return True
        
        return False

    def _is_list_item(self, line: str) -> bool:
        line = line.strip()
        if not line:
            return False
        
        for indicator in LIST_INDICATORS:
            if line.startswith(indicator):
                rest = line[len(indicator):].strip()
                if rest:
                    return True
        
        for prefix in NUMBER_PREFIX:
            if line.startswith(prefix):
                rest = line[len(prefix):].strip()
                if rest:
                    return True
        
        return False

    def _emphasize_key_points(self, line: str) -> str:
        import re
        for pattern, replacement in EMPHASIS_PATTERNS:
            line = re.sub(pattern, replacement, line)
        
        for concept in KEY_CONCEPTS:
            if concept in line:
                idx = line.index(concept)
                if idx > 0 and line[idx-1] != ' ':
                    line = line[:idx] + ' ' + line[idx:]
        
        for kw in INVALID_KEYWORDS:
            if len(kw) <= 5:
                line = re.sub(r'\b' + re.escape(kw) + r'\b', '', line)
        
        return line

    def _format_text(self, text: str) -> str:
        text = text.replace('\r\n', '\n')
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            line = line.replace('\u3000', ' ')
            
            if self._is_invalid_line(line):
                continue
            
            line = self._emphasize_key_points(line)
            cleaned_lines.append(line)
        
        if not cleaned_lines:
            return ""
        
        import re
        
        result = []
        
        for line in cleaned_lines:
            if not line:
                continue
            
            if re.match(r'^\d+[.．、)]\s*$', line):
                continue
            
            if re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]\s*$', line):
                continue
            
            if line.startswith('◆'):
                parts = re.split(r'(◆)', line)
                for part in parts:
                    if part == '◆':
                        if result and result[-1] != '':
                            result.append('')
                        result.append('◆')
                    elif part.strip():
                        result.append(f"  {part.strip()}")
                result.append('')
                continue
            
            if self._is_heading(line):
                if result and result[-1] != '':
                    result.append('')
                result.append(line)
                result.append('')
                continue
            
            if re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]\s*', line):
                result.append(f"  {line}")
                continue
            
            if re.match(r'^\d+[.．、)]\s+', line):
                result.append(f"  {line}")
                continue
            
            result.append(line)
        
        if result and result[-1] == '':
            result.pop()
        
        formatted = '\n'.join(result)
        
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        formatted = re.sub(r'^\s*list\s*$', '', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        formatted = re.sub(r'\s{2,}', ' ', formatted)
        
        lines = formatted.split('\n')
        unique_lines = []
        seen = set()
        for line in lines:
            if line.strip() and line.strip() not in seen:
                seen.add(line.strip())
                unique_lines.append(line)
        
        formatted = '\n'.join(unique_lines)
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        
        return formatted.strip()

    def extract_text(self, image_path: str) -> str:
        try:
            file_size = os.path.getsize(image_path) if os.path.exists(image_path) else 0
            print(f"[OCR] 开始识别图片: {image_path}, 文件大小: {file_size} bytes")
            
            start_time = time.time()
            result, _ = self.engine(image_path)
            elapsed = time.time() - start_time
            print(f"[OCR] OCR引擎耗时: {elapsed:.2f}s")
            
            if not result:
                print("[OCR] 未识别到任何内容")
                return ""
            
            filtered_results = []
            for item in result:
                if len(item) >= 3 and item[2] > 0.55:
                    filtered_results.append(item)
            
            print(f"[OCR] 过滤后识别结果数量: {len(filtered_results)}")
            
            filtered_results.sort(key=lambda x: (x[0][0][1], x[0][0][0]))
            
            texts = []
            for item in filtered_results:
                texts.append(item[1])
            
            raw_text = "\n".join(texts)
            print(f"[OCR] 原始文本长度: {len(raw_text)}")
            
            formatted_text = self._format_text(raw_text)
            print(f"[OCR] 格式化后文本长度: {len(formatted_text)}, 前150字符: {formatted_text[:150]}...")
            
            return formatted_text
        except Exception as e:
            print(f"[OCR] 识别失败: {e}")
            return ""

    def classify_subject(self, text: str) -> Tuple[Optional[str], float]:
        if not text:
            return None, 0.0

        text_lower = text.lower()
        scores = {}
        for subject, keywords in SUBJECT_KEYWORDS.items():
            hits = 0
            for kw in keywords:
                if kw.lower() in text_lower:
                    hits += 1
            if hits > 0:
                scores[subject] = hits

        if not scores:
            return None, 0.0

        best_subject = max(scores, key=scores.get)
        total_hits = sum(scores.values())
        confidence = scores[best_subject] / total_hits
        return best_subject, confidence

    def detect_knowledge_point(self, text: str, subject: Optional[str]) -> Optional[str]:
        if not text:
            return None

        text_lower = text.lower()
        search_dict = {}

        if subject and subject in KNOWLEDGE_POINTS:
            search_dict = KNOWLEDGE_POINTS[subject]
        else:
            for sub_points in KNOWLEDGE_POINTS.values():
                search_dict.update(sub_points)

        best_point = None
        best_hits = 0

        for point, keywords in search_dict.items():
            hits = 0
            for kw in keywords:
                if kw.lower() in text_lower:
                    hits += 1
            if hits > best_hits:
                best_hits = hits
                best_point = point

        return best_point

    def recognize(self, image_path: str) -> dict:
        full_path = str(image_path)
        
        self._clean_cache()
        cache_key = self._get_cache_key(full_path)
        
        if cache_key in self._cache:
            print(f"[OCR] 命中缓存: {cache_key}")
            return self._cache[cache_key]['data']
        
        raw_text = self.extract_text(full_path)

        if not raw_text:
            result = {
                "question_text": None,
                "subject": None,
                "knowledge_point": None,
                "confidence": 0.0,
                "raw_text": ""
            }
            self._cache[cache_key] = {"data": result, "timestamp": time.time()}
            return result

        subject, confidence = self.classify_subject(raw_text)
        knowledge_point = self.detect_knowledge_point(raw_text, subject)

        question_text = raw_text[:2000] if len(raw_text) > 2000 else raw_text

        result = {
            "question_text": question_text,
            "subject": subject,
            "knowledge_point": knowledge_point,
            "confidence": confidence,
            "raw_text": raw_text
        }
        
        self._cache[cache_key] = {"data": result, "timestamp": time.time()}
        return result

    def recognize_politics(self, image_path: str) -> dict:
        full_path = str(image_path)
        
        formatted_text = self.extract_text(full_path)
        
        if not formatted_text:
            return {"content": "", "confidence": 0.0}
        
        confidence = 0.85 if len(formatted_text) > 50 else 0.7
        if len(formatted_text) < 10:
            confidence = 0.3
        
        return {"content": formatted_text, "confidence": confidence}

ocr_service = OCRService()
