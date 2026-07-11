from typing import Optional, Tuple, List
import threading

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

class OCRService:
    def __init__(self):
        self._engine = None
        self._lock = threading.Lock()

    @property
    def engine(self):
        if self._engine is None:
            with self._lock:
                if self._engine is None:
                    from rapidocr_onnxruntime import RapidOCR
                    self._engine = RapidOCR()
        return self._engine

    def extract_text(self, image_path: str) -> str:
        try:
            result, _ = self.engine(image_path)
            if not result:
                return ""
            texts = []
            for item in result:
                if len(item) >= 3 and item[2] > 0.5:
                    texts.append(item[1])
            return "\n".join(texts)
        except Exception:
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
        raw_text = self.extract_text(image_path)

        if not raw_text:
            return {
                "question_text": None,
                "subject": None,
                "knowledge_point": None,
                "confidence": 0.0,
                "raw_text": ""
            }

        subject, confidence = self.classify_subject(raw_text)
        knowledge_point = self.detect_knowledge_point(raw_text, subject)

        question_text = raw_text[:2000] if len(raw_text) > 2000 else raw_text

        return {
            "question_text": question_text,
            "subject": subject,
            "knowledge_point": knowledge_point,
            "confidence": confidence,
            "raw_text": raw_text
        }

ocr_service = OCRService()
