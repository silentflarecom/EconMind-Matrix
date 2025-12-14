"""
Layer 2: Policy Parallel Corpus Module
Provides PDF parsing, paragraph alignment, and database operations for policy reports.

Main Components:
    - PolicyPDFParser: Parse PDF reports using Marker
    - PolicyAligner: Align paragraphs using Sentence-BERT
    - PolicyDatabase: Async database operations
    - policy_router: FastAPI endpoints

Usage:
    # Parse a PDF
    from layer2_policy import PolicyPDFParser
    parser = PolicyPDFParser()
    result = parser.parse("report.pdf", source="pboc")
    
    # Align paragraphs
    from layer2_policy import PolicyAligner
    aligner = PolicyAligner()
    alignments = aligner.align_reports(pboc_paras, fed_paras)
    
    # Add API to FastAPI app
    from layer2_policy import policy_router
    app.include_router(policy_router, prefix="/api/policy")
"""

from .models import (
    PolicyReport,
    PolicyParagraph,
    PolicyAlignment,
    ReportSource,
    ReportType,
    AlignmentMethod,
    POLICY_TOPICS,
    LAYER2_SQL_SCHEMA
)

from .pdf_parser import (
    PolicyPDFParser,
    ParseResult,
    parse_text_report
)

from .alignment import (
    PolicyAligner,
    AlignmentResult,
    FallbackAligner
)

from .database import (
    PolicyDatabase,
    init_layer2_database
)

from .api import policy_router

__all__ = [
    # Models
    "PolicyReport",
    "PolicyParagraph", 
    "PolicyAlignment",
    "ReportSource",
    "ReportType",
    "AlignmentMethod",
    "POLICY_TOPICS",
    "LAYER2_SQL_SCHEMA",
    
    # Parser
    "PolicyPDFParser",
    "ParseResult",
    "parse_text_report",
    
    # Alignment
    "PolicyAligner",
    "AlignmentResult",
    "FallbackAligner",
    
    # Database
    "PolicyDatabase",
    "init_layer2_database",
    
    # API
    "policy_router"
]

__version__ = "1.0.0"
