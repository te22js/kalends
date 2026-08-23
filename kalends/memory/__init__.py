from .base import Answer, Experience, MemorySystem, Query
from .hybrid import HybridMemory
from .structured import StructuredMemory
from .vector import VectorMemory

MEMORY_SYSTEMS = {
    "vector": VectorMemory,
    "structured": StructuredMemory,
    "hybrid": HybridMemory,
}

__all__ = ["Answer", "Experience", "MemorySystem", "Query",
           "VectorMemory", "StructuredMemory", "HybridMemory", "MEMORY_SYSTEMS"]
