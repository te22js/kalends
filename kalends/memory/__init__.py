from .base import Answer, Experience, MemorySystem, Query
from .baselines import BM25Memory, RecencyMemory, VectorMetaMemory, VectorRecencyMemory
from .hybrid import HybridMemory
from .structured import StructuredMemory
from .text_structured import TextStructuredMemory
from .vector import VectorMemory

# Registry order = column order in result tables (roughly weakest -> strongest
# by architecture sophistication; the data decides the actual ranking).
MEMORY_SYSTEMS = {
    "recency": RecencyMemory,
    "bm25": BM25Memory,
    "vector": VectorMemory,
    "vector_recency": VectorRecencyMemory,
    "vector_meta": VectorMetaMemory,
    "text_structured": TextStructuredMemory,
    "structured": StructuredMemory,
    "hybrid": HybridMemory,
}

__all__ = ["Answer", "Experience", "MemorySystem", "Query", "MEMORY_SYSTEMS",
           "RecencyMemory", "BM25Memory", "VectorMemory", "VectorRecencyMemory",
           "VectorMetaMemory", "TextStructuredMemory", "StructuredMemory",
           "HybridMemory"]
