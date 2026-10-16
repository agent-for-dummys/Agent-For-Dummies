from pathlib import Path
from langchain_core.tools import tool
from mini_pi.files import read_file
import math


def search_files(root, query, limit=5):
    words = query.casefold().split()
    if not words or limit <= 0:
        return []
    results = []
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md", ".txt"}:
            continue
        relative = path.relative_to(root).as_posix()
        try:
            text = read_file(root, relative)
        except (ValueError, UnicodeError):
            continue
        score = sum(text.casefold().count(word) for word in words)
        if score:
            results.append({"path": relative, "score": score, "excerpt": text[:300]})
    return sorted(results, key=lambda item: (-item["score"], item["path"]))[:limit]


def search_tool(root):
    @tool
    def search(query: str) -> list[dict]:
        """按关键词查找代码和文档，返回路径及摘录。"""
        return search_files(root, query)
    return search


class VectorIndex:
    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.documents = []
        self.vectors = []

    def add(self, path, text, chunk_size=500, overlap=50):
        if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
            raise ValueError("分块大小与重叠不正确")
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size-overlap)]
        vectors = self.embeddings.embed_documents(chunks) if chunks else []
        if len(vectors) != len(chunks):
            raise ValueError("向量数量和文档块不一致")
        self.documents.extend({"path": path, "text": chunk} for chunk in chunks)
        self.vectors.extend(vectors)

    def search(self, query, limit=5):
        if not self.documents or limit <= 0:
            return []
        query_vector = self.embeddings.embed_query(query)
        def similarity(vector):
            if len(vector) != len(query_vector):
                raise ValueError("向量维度不一致")
            denominator = math.sqrt(sum(x*x for x in vector)*sum(x*x for x in query_vector))
            return sum(x*y for x,y in zip(vector,query_vector))/denominator if denominator else 0.0
        ranks = sorted(enumerate(self.vectors), key=lambda pair: (-similarity(pair[1]), pair[0]))
        return [self.documents[index] for index, vector in ranks[:limit]]


def vector_tool(index):
    @tool
    def semantic_search(query: str) -> list[dict]:
        """按语义查询文档块，返回来源路径与正文片段。"""
        return index.search(query)
    return semantic_search
