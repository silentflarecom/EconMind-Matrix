"""
Layer 4 Backend Components

Core alignment engine and supporting modules.
"""

from .knowledge_cell import KnowledgeCell, TermDefinition, PolicyEvidence, SentimentEvidence
from .data_loader import DataLoader
from .alignment_engine import AlignmentEngine

__all__ = [
    "KnowledgeCell",
    "TermDefinition", 
    "PolicyEvidence",
    "SentimentEvidence",
    "DataLoader",
    "AlignmentEngine",
]
