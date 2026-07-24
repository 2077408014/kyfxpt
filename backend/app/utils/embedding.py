import os
import re
import math
from typing import List, Optional

os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

HAS_EMBEDDING = False
np = None


class SimpleEmbedder:
    def __init__(self, dim: int = 384):
        self.dim = dim
        self.vocab = {}
        self.idf = {}

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r'[a-zA-Z]+[\w]*|[\u4e00-\u9fff]+', text)
        return [t for t in tokens if len(t) >= 2]

    def _build_vocab(self, texts: List[str]):
        doc_count = len(texts)
        for text in texts:
            tokens = set(self._tokenize(text))
            for token in tokens:
                self.vocab[token] = self.vocab.get(token, 0) + 1
                self.idf[token] = math.log(doc_count / (self.vocab[token] + 1))

    def _text_to_vec(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        tokens = self._tokenize(text)
        if not tokens:
            return vec

        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1

        for i, token in enumerate(self.vocab.keys()):
            idx = hash(token) % self.dim
            tfidf = tf.get(token, 0) * self.idf.get(token, 0)
            vec[idx] += tfidf

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]

        return vec

    def embed_text(self, text: str):
        if not self.vocab:
            self._build_vocab([text])
        return self._text_to_vec(text)

    def embed_texts(self, texts: List[str]):
        self._build_vocab(texts)
        return [self._text_to_vec(text) for text in texts]

    def similarity(self, vec1, vec2) -> float:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)


class TextEmbedder:
    def __init__(self, model_name: str = "simple-tfidf"):
        self.model_name = model_name
        self.simple_embedder = SimpleEmbedder()

    def embed_text(self, text: str):
        return self.simple_embedder.embed_text(text)

    def embed_texts(self, texts: List[str]):
        return self.simple_embedder.embed_texts(texts)

    def similarity(self, vec1, vec2) -> float:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)


text_embedder = None


def get_text_embedder() -> TextEmbedder:
    global text_embedder
    if text_embedder is None:
        text_embedder = TextEmbedder()
    return text_embedder