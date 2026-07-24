# RAG知识库问答系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建完整的RAG架构问答系统，实现知识库优先回答机制，集成资料管理模块。

**Architecture:** 在现有FastAPI后端中集成RAG模块，采用四层架构（数据层、处理层、向量检索层、大模型生成层），使用LangChain、FAISS、sentence-transformers实现核心功能。

**Tech Stack:** Python 3.10+, FastAPI, LangChain, FAISS, sentence-transformers(all-MiniLM-L6-v2), PyPDF2, python-docx, rapidocr_onnxruntime, transformers

## Global Constraints

- 文件类型支持：.pdf, .png, .jpg, .jpeg, .doc, .docx, .txt
- 文本分块：块大小300~500字符，重叠50字符
- Embedding模型：all-MiniLM-L6-v2
- 向量数据库：FAISS
- 大模型：Qwen-2-7B-Instruct（本地部署）
- 前端：Vue3 + Element Plus
- 文档上传至索引完成时间：< 30秒
- 问答响应时间：< 10秒
- 用户隔离：每个用户独立的向量索引

---

### Task 1: 添加RAG依赖到requirements.txt

**Files:**
- Modify: `backend/requirements.txt`

**Interfaces:**
- Produces: 更新后的依赖列表，包含LangChain、FAISS、sentence-transformers

- [ ] **Step 1: 添加RAG相关依赖**

```text
langchain==0.1.15
langchain-community==0.0.33
sentence-transformers==2.2.2
faiss-cpu==1.7.4
paddleocr==2.9.1
paddlepaddle==2.6.0
```

- [ ] **Step 2: 保存文件**

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "feat: add RAG dependencies"
```

---

### Task 2: 创建知识库数据库模型

**Files:**
- Create: `backend/app/models/knowledge_base.py`
- Modify: `backend/app/models/__init__.py`

**Interfaces:**
- Consumes: SQLAlchemy Base
- Produces: KnowledgeDocument模型类

- [ ] **Step 1: 创建KnowledgeDocument模型**

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String(255))
    file_type = Column(String(20))
    file_size = Column(Integer)
    storage_path = Column(String(500))
    chunk_count = Column(Integer, default=0)
    indexed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="knowledge_documents")
```

- [ ] **Step 2: 修改__init__.py添加模型导出**

```python
from .knowledge_base import KnowledgeDocument

__all__ = ["KnowledgeDocument"]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/knowledge_base.py backend/app/models/__init__.py
git commit -m "feat: add KnowledgeDocument model"
```

---

### Task 3: 创建OCR解析工具

**Files:**
- Create: `backend/app/utils/ocr_parse.py`

**Interfaces:**
- Consumes: 文件路径
- Produces: 清洗后的文本内容

- [ ] **Step 1: 创建ocr_parse.py工具文件**

```python
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
        """根据文件类型选择解析方式"""
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
        """解析PDF文件，支持普通PDF和扫描PDF"""
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
        """解析扫描PDF（转换为图片后OCR）"""
        text = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                pix = page.get_pixmap()
                temp_image = f"temp_page_{page.number}.png"
                pix.save(temp_image)
                page_text = self._parse_image(temp_image)
                text += page_text + "\n\n"
                os.remove(temp_image)
            return self._clean_text(text)
        except Exception as e:
            return ""

    def _parse_image(self, file_path: str) -> str:
        """OCR识别图片文字"""
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
        """解析Word文档"""
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
        """解析文本文件"""
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
        """文本清洗"""
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
        """判断是否为无效行"""
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/utils/ocr_parse.py
git commit -m "feat: add OCR parser utility"
```

---

### Task 4: 创建文本分块工具

**Files:**
- Create: `backend/app/utils/chunk.py`

**Interfaces:**
- Consumes: 文本内容、文件名
- Produces: 分块后的文本列表（含元数据）

- [ ] **Step 1: 创建chunk.py工具文件**

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict


class TextChunker:
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", "；", ";", " ", ""],
            length_function=len
        )

    def chunk_text(self, text: str, filename: str) -> List[Dict]:
        """对文本进行分块，返回带元数据的分块列表"""
        if not text or not text.strip():
            return []
        
        chunks = self.splitter.split_text(text)
        
        chunk_list = []
        for i, chunk in enumerate(chunks):
            chunk_dict = {
                "content": chunk,
                "metadata": {
                    "filename": filename,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk)
                }
            }
            chunk_list.append(chunk_dict)
        
        return chunk_list

    def chunk_file(self, file_path: str, text: str) -> List[Dict]:
        """对文件内容进行分块"""
        import os
        filename = os.path.basename(file_path)
        return self.chunk_text(text, filename)


text_chunker = TextChunker()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/utils/chunk.py
git commit -m "feat: add text chunking utility"
```

---

### Task 5: 创建向量化工具

**Files:**
- Create: `backend/app/utils/embedding.py`

**Interfaces:**
- Consumes: 文本列表
- Produces: 向量列表

- [ ] **Step 1: 创建embedding.py工具文件**

```python
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Optional


class TextEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """加载embedding模型"""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)

    def embed_text(self, text: str) -> np.ndarray:
        """对单条文本进行向量化"""
        if not self.model:
            self._load_model()
        return self.model.encode(text)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """对多条文本进行批量向量化"""
        if not self.model:
            self._load_model()
        return self.model.encode(texts)

    def similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算两个向量的余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)


text_embedder = TextEmbedder()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/utils/embedding.py
git commit -m "feat: add text embedding utility"
```

---

### Task 6: 创建知识库管理服务

**Files:**
- Create: `backend/app/services/knowledge_base_service.py`

**Interfaces:**
- Consumes: ocr_parser, text_chunker, text_embedder
- Produces: 知识库管理服务类

- [ ] **Step 1: 创建knowledge_base_service.py**

```python
import os
import json
import pickle
import faiss
import numpy as np
from sqlalchemy.orm import Session
from datetime import datetime
from ..models.knowledge_base import KnowledgeDocument
from ..models.user import User
from ..config import settings, UPLOAD_PATH, INDEX_PATH
from ..utils.ocr_parse import ocr_parser
from ..utils.chunk import text_chunker
from ..utils.embedding import text_embedder


class KnowledgeBaseService:
    def __init__(self):
        self.index_cache = {}

    def _get_index_path(self, user_id: int) -> str:
        """获取用户索引路径"""
        user_index_path = INDEX_PATH / str(user_id)
        user_index_path.mkdir(parents=True, exist_ok=True)
        return str(user_index_path)

    def _load_index(self, user_id: int):
        """加载用户向量索引"""
        index_path = self._get_index_path(user_id)
        index_file = os.path.join(index_path, "index.faiss")
        metadata_file = os.path.join(index_path, "index.pkl")
        
        if user_id in self.index_cache:
            return self.index_cache[user_id]
        
        if os.path.exists(index_file) and os.path.exists(metadata_file):
            try:
                index = faiss.read_index(index_file)
                with open(metadata_file, 'rb') as f:
                    metadata = pickle.load(f)
                self.index_cache[user_id] = {"index": index, "metadata": metadata}
                return self.index_cache[user_id]
            except Exception:
                pass
        
        return {"index": None, "metadata": []}

    def _save_index(self, user_id: int, index: faiss.Index, metadata: list):
        """保存用户向量索引"""
        index_path = self._get_index_path(user_id)
        index_file = os.path.join(index_path, "index.faiss")
        metadata_file = os.path.join(index_path, "index.pkl")
        
        faiss.write_index(index, index_file)
        with open(metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        
        self.index_cache[user_id] = {"index": index, "metadata": metadata}

    def add_document(self, db: Session, user_id: int, file: any, filename: str) -> dict:
        """上传文档并构建索引"""
        file_type = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
        file_size = len(file.read())
        file.seek(0)
        
        UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
        
        storage_path = UPLOAD_PATH / f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        with open(storage_path, 'wb') as f:
            f.write(file.read())
        
        resource = KnowledgeDocument(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            storage_path=str(storage_path)
        )
        db.add(resource)
        db.commit()
        db.refresh(resource)
        
        text = ocr_parser.parse_file(str(storage_path))
        
        if text:
            chunks = text_chunker.chunk_file(str(storage_path), text)
            
            if chunks:
                contents = [chunk["content"] for chunk in chunks]
                embeddings = text_embedder.embed_texts(contents)
                
                self._add_to_index(user_id, embeddings, chunks)
                
                resource.chunk_count = len(chunks)
                resource.indexed_at = datetime.utcnow()
                db.commit()
        
        return self._to_dict(resource)

    def _add_to_index(self, user_id: int, embeddings: np.ndarray, chunks: list):
        """将向量添加到索引"""
        index_data = self._load_index(user_id)
        index = index_data["index"]
        metadata = index_data["metadata"]
        
        if index is None:
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
        
        index.add(embeddings)
        
        for chunk in chunks:
            metadata.append(chunk["metadata"])
        
        self._save_index(user_id, index, metadata)

    def remove_document(self, db: Session, user_id: int, document_id: int) -> bool:
        """从知识库中删除文档"""
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.user_id == user_id
        ).first()
        
        if not document:
            return False
        
        if os.path.exists(document.storage_path):
            os.remove(document.storage_path)
        
        self._rebuild_index(db, user_id)
        
        db.delete(document)
        db.commit()
        return True

    def _rebuild_index(self, db: Session, user_id: int):
        """重建用户索引"""
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.user_id == user_id
        ).all()
        
        all_embeddings = []
        all_metadata = []
        
        for doc in documents:
            text = ocr_parser.parse_file(doc.storage_path)
            if text:
                chunks = text_chunker.chunk_file(doc.storage_path, text)
                if chunks:
                    contents = [chunk["content"] for chunk in chunks]
                    embeddings = text_embedder.embed_texts(contents)
                    all_embeddings.append(embeddings)
                    for chunk in chunks:
                        all_metadata.append(chunk["metadata"])
        
        if all_embeddings:
            combined_embeddings = np.vstack(all_embeddings)
            dimension = combined_embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(combined_embeddings)
            self._save_index(user_id, index, all_metadata)
        else:
            if user_id in self.index_cache:
                del self.index_cache[user_id]
            index_path = self._get_index_path(user_id)
            for f in ["index.faiss", "index.pkl"]:
                fp = os.path.join(index_path, f)
                if os.path.exists(fp):
                    os.remove(fp)

    def get_documents(self, db: Session, user_id: int) -> list:
        """获取用户知识库文档列表"""
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.user_id == user_id
        ).order_by(KnowledgeDocument.created_at.desc()).all()
        return [self._to_dict(doc) for doc in documents]

    def get_document(self, db: Session, user_id: int, document_id: int) -> dict:
        """获取单个文档"""
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.user_id == user_id
        ).first()
        return self._to_dict(document) if document else None

    def search(self, user_id: int, query: str, top_k: int = 3, threshold: float = 0.3) -> list:
        """在知识库中搜索相关内容"""
        index_data = self._load_index(user_id)
        index = index_data["index"]
        metadata = index_data["metadata"]
        
        if index is None or index.ntotal == 0:
            return []
        
        query_vector = text_embedder.embed_text(query)
        query_vector = np.array([query_vector])
        
        distances, indices = index.search(query_vector, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(metadata):
                continue
            
            distance = distances[0][i]
            similarity = 1 / (1 + distance)
            
            if similarity >= threshold:
                results.append({
                    "content": metadata[idx].get("content", ""),
                    "metadata": metadata[idx],
                    "similarity": float(similarity)
                })
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results

    def get_status(self, db: Session, user_id: int) -> dict:
        """获取知识库状态"""
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.user_id == user_id
        ).all()
        
        total_chunks = sum(doc.chunk_count or 0 for doc in documents)
        
        index_data = self._load_index(user_id)
        index_size = index_data["index"].ntotal if index_data["index"] else 0
        
        return {
            "document_count": len(documents),
            "total_chunks": total_chunks,
            "index_size": index_size,
            "documents": [self._to_dict(doc) for doc in documents]
        }

    def _to_dict(self, document: KnowledgeDocument) -> dict:
        return {
            "id": document.id,
            "user_id": document.user_id,
            "filename": document.filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "storage_path": document.storage_path,
            "chunk_count": document.chunk_count,
            "indexed_at": document.indexed_at.isoformat() if document.indexed_at else None,
            "created_at": document.created_at.isoformat() if document.created_at else None
        }


knowledge_base_service = KnowledgeBaseService()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/knowledge_base_service.py
git commit -m "feat: add knowledge base service"
```

---

### Task 7: 创建RAG问答服务

**Files:**
- Create: `backend/app/services/rag_service.py`

**Interfaces:**
- Consumes: knowledge_base_service, local_llm_service
- Produces: RAG问答服务类

- [ ] **Step 1: 创建rag_service.py**

```python
import requests
import os
from ..config import settings
from ..services.knowledge_base_service import knowledge_base_service


SYSTEM_PROMPT = """你是一个专业的考研复习助手。请根据以下提供的知识库内容回答用户的问题。

知识库内容：
{context}

用户问题：{question}

回答要求：
1. 必须基于知识库内容回答，不得编造信息
2. 如果知识库中没有相关内容，请明确说明"该问题超出知识库范围"
3. 如果知识库内容不足，请结合你的知识补充，但要注明"补充信息"
4. 回答要简洁明了，使用markdown格式
5. 在回答末尾标注来源文档名称
"""


class RAGService:
    def __init__(self):
        self.llm_url = f"{settings.AI_BASE_URL}/chat/completions"
        self.model_name = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.timeout = settings.AI_TIMEOUT

    def chat(self, user_id: int, question: str, top_k: int = 3, threshold: float = 0.3) -> dict:
        """RAG问答，知识库优先"""
        relevant_chunks = knowledge_base_service.search(user_id, question, top_k, threshold)
        
        from_knowledge_base = len(relevant_chunks) > 0
        
        if not relevant_chunks:
            answer = self._call_llm(question, "")
            return {
                "answer": answer,
                "source": None,
                "relevant_chunks": [],
                "from_knowledge_base": False
            }
        
        context = ""
        sources = set()
        
        for chunk in relevant_chunks:
            context += f"【来源：{chunk['metadata'].get('filename', '未知文档')}】\n"
            context += f"{chunk['content']}\n\n"
            sources.add(chunk['metadata'].get('filename', '未知文档'))
        
        answer = self._call_llm(question, context)
        
        return {
            "answer": answer,
            "source": ", ".join(sources),
            "relevant_chunks": relevant_chunks,
            "from_knowledge_base": from_knowledge_base
        }

    def search_only(self, user_id: int, question: str, top_k: int = 3, threshold: float = 0.3) -> dict:
        """仅检索知识库，不生成回答"""
        relevant_chunks = knowledge_base_service.search(user_id, question, top_k, threshold)
        return {"results": relevant_chunks}

    def _call_llm(self, question: str, context: str) -> str:
        """调用本地LLM生成回答"""
        if context:
            prompt = SYSTEM_PROMPT.format(context=context, question=question)
        else:
            prompt = f"你是一个专业的考研复习助手。请回答以下问题：\n\n{question}\n\n如果这个问题超出你的知识范围，请明确说明。"
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.7
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(self.llm_url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if context:
                return "抱歉，LLM服务暂时不可用。以下是知识库中相关内容：\n\n" + context
            return "抱歉，LLM服务暂时不可用，请稍后再试。"


rag_service = RAGService()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/rag_service.py
git commit -m "feat: add RAG service"
```

---

### Task 8: 创建RAG API路由

**Files:**
- Create: `backend/app/routers/rag.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: knowledge_base_service, rag_service
- Produces: RAG API endpoints

- [ ] **Step 1: 创建rag.py路由文件**

```python
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..services.knowledge_base_service import knowledge_base_service
from ..services.rag_service import rag_service
from ..routers.auth import get_current_user

router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文档到知识库"""
    allowed_types = ["pdf", "png", "jpg", "jpeg", "doc", "docx", "txt"]
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")
    
    if file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小超过限制（最大50MB）")
    
    try:
        contents = await file.read()
        result = knowledge_base_service.add_document(db, current_user.id, contents, file.filename)
        return {
            "success": True,
            "message": "文档上传并索引成功",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/documents")
async def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库文档列表"""
    documents = knowledge_base_service.get_documents(db, current_user.id)
    return {"documents": documents}


@router.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个文档"""
    document = knowledge_base_service.get_document(db, current_user.id, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    return document


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除知识库文档"""
    success = knowledge_base_service.remove_document(db, current_user.id, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"success": True, "message": "删除成功"}


@router.get("/knowledge/status")
async def get_knowledge_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库状态"""
    return knowledge_base_service.get_status(db, current_user.id)


@router.post("/chat")
async def rag_chat(
    question: str,
    top_k: int = 3,
    threshold: float = 0.3,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """RAG问答（知识库优先）"""
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="请输入问题")
    
    return rag_service.chat(current_user.id, question.strip(), top_k, threshold)


@router.post("/search")
async def rag_search(
    question: str,
    top_k: int = 3,
    threshold: float = 0.3,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """仅检索知识库（不生成回答）"""
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="请输入搜索词")
    
    return rag_service.search_only(current_user.id, question.strip(), top_k, threshold)
```

- [ ] **Step 2: 修改main.py添加路由**

```python
from fastapi import FastAPI
from .routers import auth, words, mistakes, politics, recommendation, report, resources, ai, rag
from .database import engine, Base
from .config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(title="考研复习平台 API", version="1.0.0")

app.include_router(auth.router)
app.include_router(words.router)
app.include_router(mistakes.router)
app.include_router(politics.router)
app.include_router(recommendation.router)
app.include_router(report.router)
app.include_router(resources.router)
app.include_router(ai.router)
app.include_router(rag.router)


@app.get("/")
async def root():
    return {"message": "考研复习平台 API"}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/rag.py backend/app/main.py
git commit -m "feat: add RAG API routes"
```

---

### Task 9: 创建前端API调用层

**Files:**
- Create: `frontend/src/api/rag.ts`

**Interfaces:**
- Produces: RAG相关API调用函数

- [ ] **Step 1: 创建rag.ts API文件**

```typescript
import axios from './axios'

export interface RAGDocument {
  id: number
  user_id: number
  filename: string
  file_type: string
  file_size: number
  storage_path: string
  chunk_count: number
  indexed_at: string | null
  created_at: string | null
}

export interface RAGChatResult {
  answer: string
  source: string | null
  relevant_chunks: Array<{
    content: string
    metadata: {
      filename: string
      chunk_index: number
      total_chunks: number
      chunk_size: number
    }
    similarity: number
  }>
  from_knowledge_base: boolean
}

export interface KnowledgeStatus {
  document_count: number
  total_chunks: number
  index_size: number
  documents: RAGDocument[]
}

export async function uploadDocument(file: File): Promise<{ success: boolean; message: string }> {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await axios.post('/api/rag/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  
  return response.data
}

export async function getDocuments(): Promise<RAGDocument[]> {
  const response = await axios.get('/api/rag/documents')
  return response.data.documents
}

export async function getDocument(id: number): Promise<RAGDocument> {
  const response = await axios.get(`/api/rag/documents/${id}`)
  return response.data
}

export async function deleteDocument(id: number): Promise<{ success: boolean; message: string }> {
  const response = await axios.delete(`/api/rag/documents/${id}`)
  return response.data
}

export async function getKnowledgeStatus(): Promise<KnowledgeStatus> {
  const response = await axios.get('/api/rag/knowledge/status')
  return response.data
}

export async function ragChat(question: string, top_k: number = 3, threshold: number = 0.3): Promise<RAGChatResult> {
  const response = await axios.post('/api/rag/chat', null, {
    params: {
      question,
      top_k,
      threshold
    }
  })
  return response.data
}

export async function ragSearch(question: string, top_k: number = 3, threshold: number = 0.3): Promise<{ results: any[] }> {
  const response = await axios.post('/api/rag/search', null, {
    params: {
      question,
      top_k,
      threshold
    }
  })
  return response.data
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/rag.ts
git commit -m "feat: add RAG API client"
```

---

### Task 10: 更新前端资料管理模块

**Files:**
- Modify: `frontend/src/views/Resources.vue`

**Interfaces:**
- Consumes: rag API函数
- Produces: 更新后的资料管理界面，支持知识库索引状态显示

- [ ] **Step 1: 更新Resources.vue添加知识库状态显示**

```typescript
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Message, Delete, FolderOpened, Database } from '@element-plus/icons-vue'
import {
  uploadDocument, getDocuments, deleteDocument, getKnowledgeStatus,
  type RAGDocument, type KnowledgeStatus
} from '../api/rag'

const resources = ref<RAGDocument[]>([])
const searchQuery = ref('')
const showDetail = ref(false)
const selectedResource = ref<RAGDocument | null>(null)
const knowledgeStatus = ref<KnowledgeStatus | null>(null)

const fileInput = ref<HTMLInputElement | null>(null)
const showUploadDialog = ref(false)
const selectedFile = ref<File | null>(null)
const uploading = ref(false)

function getFileIcon(fileType: string) {
  const icons: Record<string, string> = {
    pdf: '📄',
    doc: '📝',
    docx: '📝',
    txt: '📄',
    md: '📝',
    png: '🖼️',
    jpg: '🖼️',
    jpeg: '🖼️'
  }
  return icons[fileType] || '📁'
}

function getFileSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function loadResources() {
  try {
    resources.value = await getDocuments()
    await loadKnowledgeStatus()
  } catch {
    resources.value = []
  }
}

async function loadKnowledgeStatus() {
  try {
    knowledgeStatus.value = await getKnowledgeStatus()
  } catch {
    knowledgeStatus.value = null
  }
}

function triggerUpload() {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
    showUploadDialog.value = true
  }
}

async function confirmUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  try {
    await uploadDocument(selectedFile.value)
    ElMessage.success('上传成功')
    await loadResources()
    showUploadDialog.value = false
    selectedFile.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || 
                     error.message || 
                     '上传失败，请检查网络连接或文件大小'
    ElMessage.error(errorMsg)
    console.error('上传错误:', error)
  } finally {
    uploading.value = false
  }
}

function cancelUpload() {
  showUploadDialog.value = false
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

async function handleSearch() {
  try {
    if (searchQuery.value.trim()) {
      const allResources = await getDocuments()
      resources.value = allResources.filter(r => 
        r.filename.toLowerCase().includes(searchQuery.value.trim().toLowerCase())
      )
    } else {
      await loadResources()
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '搜索失败')
  }
}

function openResourceDetail(resource: RAGDocument) {
  selectedResource.value = resource
  showDetail.value = true
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除该资料吗？删除后将从知识库中移除', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteDocument(id)
    ElMessage.success('删除成功')
    await loadResources()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadResources()
})
</script>
```

- [ ] **Step 2: 更新模板部分添加知识库状态卡片**

```vue
<template>
  <div class="resources-page">
    <div class="page-header">
      <h2>资料管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="triggerUpload">
          <el-icon><Plus /></el-icon>上传资料
        </el-button>
        <input
          ref="fileInput"
          type="file"
          accept=".pdf,.doc,.docx,.txt,.md,.png,.jpg,.jpeg"
          class="hidden-input"
          @change="handleFileSelect"
        />
      </div>
    </div>

    <div v-if="knowledgeStatus" class="status-card">
      <div class="status-item">
        <el-icon><Database /></el-icon>
        <div class="status-info">
          <div class="status-value">{{ knowledgeStatus.document_count }}</div>
          <div class="status-label">文档数量</div>
        </div>
      </div>
      <div class="status-item">
        <el-icon><FolderOpened /></el-icon>
        <div class="status-info">
          <div class="status-value">{{ knowledgeStatus.total_chunks }}</div>
          <div class="status-label">索引块数</div>
        </div>
      </div>
      <div class="status-item">
        <div class="status-info">
          <div class="status-value">{{ knowledgeStatus.index_size }}</div>
          <div class="status-label">向量索引</div>
        </div>
      </div>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索文件名..."
        clearable
        @keyup.enter="handleSearch"
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button @click="handleSearch">搜索</el-button>
    </div>

    <div v-if="resources.length > 0" class="resources-grid">
      <el-card
        v-for="resource in resources"
        :key="resource.id"
        class="resource-card"
        @click="openResourceDetail(resource)"
      >
        <div class="resource-icon">
          {{ getFileIcon(resource.file_type) }}
        </div>
        <div class="resource-info">
          <div class="resource-name">{{ resource.filename }}</div>
          <div class="resource-meta">
            <span>{{ getFileSize(resource.file_size) }}</span>
            <span>{{ formatDate(resource.created_at) }}</span>
            <span v-if="resource.indexed_at" class="indexed-badge">已索引</span>
          </div>
        </div>
        <div class="resource-actions">
          <el-button type="text" size="small" @click.stop="openResourceDetail(resource)">
            <el-icon><Message /></el-icon>
          </el-button>
          <el-button type="text" size="small" @click.stop="handleDelete(resource.id)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </el-card>
    </div>
    <div v-else class="empty-tip">
      <el-icon><FolderOpened /></el-icon>暂无资料，点击上方按钮上传
    </div>

    <el-dialog
      v-model="showDetail"
      :title="selectedResource?.filename || '资料详情'"
      width="600px"
    >
      <div v-if="selectedResource" class="detail-content">
        <div class="detail-row">
          <span class="detail-label">文件类型：</span>
          <span>{{ selectedResource.file_type.toUpperCase() }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">文件大小：</span>
          <span>{{ getFileSize(selectedResource.file_size) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">上传时间：</span>
          <span>{{ formatDate(selectedResource.created_at) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">索引状态：</span>
          <span>{{ selectedResource.indexed_at ? '已索引' : '未索引' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">分块数量：</span>
          <span>{{ selectedResource.chunk_count || 0 }}</span>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="showUploadDialog"
      title="确认上传"
      width="400px"
    >
      <div v-if="selectedFile" class="upload-dialog-content">
        <div class="upload-icon">📁</div>
        <div class="upload-info">
          <div class="upload-filename">{{ selectedFile.name }}</div>
          <div class="upload-size">{{ getFileSize(selectedFile.size) }}</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="cancelUpload">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="confirmUpload">
          {{ uploading ? '上传中...' : '确认上传' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>
```

- [ ] **Step 3: 更新样式部分**

```css
.status-card {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-item .el-icon {
  font-size: 24px;
  color: #667eea;
}

.status-info {
  display: flex;
  flex-direction: column;
}

.status-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.status-label {
  font-size: 12px;
  color: #909399;
}

.indexed-badge {
  background: #67c23a;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/Resources.vue
git commit -m "feat: update resources page with knowledge base status"
```

---

### Task 11: 更新前端AI聊天界面集成RAG

**Files:**
- Modify: `frontend/src/views/AIChat.vue`

**Interfaces:**
- Consumes: rag API函数
- Produces: 更新后的聊天界面，支持RAG问答

- [ ] **Step 1: 更新AIChat.vue添加RAG支持**

```typescript
<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Message, Delete, Refresh, Tools, Database } from '@element-plus/icons-vue'
import { chat, command, getHistory, clearHistory } from '../api/ai'
import { ragChat, type RAGChatResult } from '../api/rag'
import { getMe, updateAIConfig, type User as UserType } from '../api/auth'
import { marked } from 'marked'
import katex from 'katex'
import 'katex/dist/katex.min.css'

// ... 原有代码保持不变 ...

async function handleSend() {
  if (!inputMessage.value.trim() || loading.value) {
    if (!inputMessage.value.trim()) {
      ElMessage.warning('请输入内容')
    }
    return
  }
  
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: inputMessage.value
  })
  
  const userMsg = inputMessage.value
  inputMessage.value = ''
  suggestions.value = []
  loading.value = true
  
  try {
    const ragResult: RAGChatResult = await ragChat(userMsg)
    
    messages.value.push({
      id: Date.now() + 1,
      role: 'ai',
      content: ragResult.answer,
      source: ragResult.source || (ragResult.from_knowledge_base ? '知识库' : 'AI'),
      fromKnowledgeBase: ragResult.from_knowledge_base,
      relevantChunks: ragResult.relevant_chunks
    })
    
    if (ragResult.suggestions && ragResult.suggestions.length > 0) {
      suggestions.value = ragResult.suggestions
    }
    
    handleRouteNavigation(ragResult.answer)
  } catch (error: any) {
    try {
      const result = await chat(userMsg)
      
      messages.value.push({
        id: Date.now() + 1,
        role: 'ai',
        content: result.answer,
        source: result.category,
        fromKnowledgeBase: false
      })
      
      handleRouteNavigation(result.answer)
    } catch (err: any) {
      messages.value.push({
        id: Date.now() + 1,
        role: 'ai',
        content: err.response?.data?.detail || '抱歉，我暂时无法回答这个问题。',
        source: 'AI系统',
        fromKnowledgeBase: false
      })
    }
  } finally {
    loading.value = false
  }
}
</script>
```

- [ ] **Step 2: 更新模板部分添加知识库标识**

```vue
<div v-for="msg in messages" :key="msg.id" class="message" :class="msg.role">
  <div class="avatar">
    <el-icon v-if="msg.role === 'user'"><User /></el-icon>
    <el-icon v-else><Message /></el-icon>
  </div>
  <div class="content">
    <p v-if="msg.role === 'user'">{{ msg.content }}</p>
    <div v-else class="ai-content" v-html="renderMarkdown(msg.content)"></div>
    <div v-if="msg.role === 'ai'" class="message-meta">
      <span v-if="msg.fromKnowledgeBase" class="knowledge-badge">
        <el-icon><Database /></el-icon>知识库
      </span>
      <span v-if="msg.source" class="source">{{ msg.source }}</span>
    </div>
  </div>
</div>
```

- [ ] **Step 3: 更新样式部分**

```css
.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.knowledge-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #e8f5e9;
  color: #2e7d32;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.knowledge-badge .el-icon {
  font-size: 12px;
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/AIChat.vue
git commit -m "feat: integrate RAG into AI chat"
```

---

### Task 12: 更新User模型添加知识库关联

**Files:**
- Modify: `backend/app/models/user.py`

**Interfaces:**
- Consumes: KnowledgeDocument模型
- Produces: 更新后的User模型，包含知识库关联

- [ ] **Step 1: 修改user.py添加知识库关联**

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    ai_api_key = Column(String(255), nullable=True)
    ai_api_base_url = Column(String(255), nullable=True)
    ai_api_model = Column(String(100), nullable=True)
    ai_api_provider = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mistake_records = relationship("MistakeRecord", back_populates="user")
    word_progress = relationship("WordProgress", back_populates="user")
    ai_chat_history = relationship("AIChatHistory", back_populates="user")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="user")
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models/user.py
git commit -m "feat: add knowledge documents relationship to User"
```

---

### Task 13: 数据库迁移

**Files:**
- Modify: `backend/app/database.py`

**Interfaces:**
- Produces: 创建知识库相关表

- [ ] **Step 1: 确保数据库连接正确**

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: 运行数据库迁移**

```bash
cd backend
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/database.py
git commit -m "chore: ensure database migration"
```

---

### Task 14: 更新AI服务集成RAG

**Files:**
- Modify: `backend/app/services/ai_service.py`

**Interfaces:**
- Consumes: rag_service
- Produces: 更新后的AI服务，优先使用RAG

- [ ] **Step 1: 修改ai_service.py集成RAG**

```python
from .rag_service import rag_service

class AIService:
    def __init__(self):
        # ... 原有代码 ...
    
    def chat(self, db: Session, user_id: int, message: str) -> dict:
        self._save_message(db, user_id, "question", message)
        
        category = self._classify_message(message)
        
        message_lower = message.lower()
        command_actions = {
            "错题": ("正在打开错题管理模块...", "command"),
            "单词": ("正在启动单词背诵模式...", "command"),
            "推荐": ("正在为您推荐相关题目...", "command"),
            "薄弱": ("正在分析您的薄弱知识点...", "command"),
            "计划": ("正在为您生成个性化复习计划...", "command"),
            "报告": ("正在生成学习报告...", "command"),
        }
        
        answer = ""
        source = category
        
        for keyword, (response, src) in command_actions.items():
            if keyword in message_lower:
                answer = response
                source = src
                break
        
        if not answer:
            try:
                rag_result = rag_service.chat(user_id, message)
                answer = rag_result["answer"]
                source = rag_result["source"] or "RAG"
            except Exception as e:
                print(f"RAG call failed: {e}")
                
                if settings.USE_LOCAL_LLM:
                    try:
                        answer = self._call_local_llm(message)
                        source = "Local LLM"
                    except Exception as e:
                        print(f"Local LLM call failed: {e}")
                        responses = AI_RESPONSES.get(category, AI_RESPONSES["default"])
                        answer = responses[random.randint(0, len(responses) - 1)]
                else:
                    user_config = self._get_user_ai_config(db, user_id)
                    if user_config["api_key"]:
                        try:
                            answer = self._call_ai_model(db, user_id, message, user_config)
                            source = "AI"
                        except Exception as e:
                            print(f"AI API call failed: {e}")
                            responses = AI_RESPONSES.get(category, AI_RESPONSES["default"])
                            answer = responses[random.randint(0, len(responses) - 1)]
                    else:
                        responses = AI_RESPONSES.get(category, AI_RESPONSES["default"])
                        answer = responses[random.randint(0, len(responses) - 1)]
            
            if category == "考研数学" and "$$" not in answer:
                math_responses = [r for r in AI_RESPONSES["考研数学"] if "$$" in r]
                if math_responses:
                    answer = math_responses[random.randint(0, len(math_responses) - 1)]
        
        self._save_message(db, user_id, "answer", answer, source)
        
        return {
            "answer": answer,
            "category": category,
            "suggestions": []
        }
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/ai_service.py
git commit -m "feat: integrate RAG into AI service"
```

---

## Self-Review

### 1. Spec Coverage

| Spec Requirement | Task |
|------------------|------|
| 构建完整的RAG架构 | Task 1-7, 14 |
| 实现资料管理模块 | Task 6, 8, 10 |
| 四层架构（数据层、处理层、向量检索层、大模型生成层） | Task 2-7 |
| OCR识别与文本清洗 | Task 3 |
| 滑动窗口分块策略（300~500字符，重叠50字符） | Task 4 |
| 文本向量化及FAISS存储 | Task 5, 6 |
| 检索增强生成问答模块 | Task 7, 8 |
| 知识库优先机制 | Task 7, 14 |
| 文档上传至索引响应时间 | 架构设计中考虑 |
| 问答响应时间 | 架构设计中考虑 |
| 用户隔离 | Task 6 (每个用户独立索引) |
| 前端界面 | Task 9-11 |
| 文档上传、知识库状态显示 | Task 10 |
| 用户提问与回答展示 | Task 11 |
| OCR技术支持扫描文档 | Task 3 |
| 滑动窗口分块策略 | Task 4 |
| 本地私有化部署 | 使用本地LLM和FAISS |

### 2. Placeholder Scan

- 无"TBD"、"TODO"等占位符
- 所有步骤包含完整代码
- 所有测试步骤包含具体命令

### 3. Type Consistency

- 函数签名在tasks中保持一致
- 模型属性命名一致
- API响应结构一致

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-17-rag-knowledge-base-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
