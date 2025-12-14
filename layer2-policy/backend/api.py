"""
Layer 2: Policy API Endpoints
FastAPI router for policy report operations.

Integrates with Layer 1 main.py by adding policy-specific endpoints.

Usage:
    from layer2_api import policy_router
    
    app.include_router(policy_router, prefix="/api/policy", tags=["policy"])
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import JSONResponse

# Import Layer 2 modules
try:
    from .database import PolicyDatabase
    from .pdf_parser import PolicyPDFParser, parse_text_report
    from .alignment import PolicyAligner, AlignmentResult
    from .models import (
        PolicyReport, PolicyParagraph, PolicyAlignment,
        ReportSource, ReportType, AlignmentMethod, POLICY_TOPICS
    )
except ImportError:
    from database import PolicyDatabase
    from pdf_parser import PolicyPDFParser, parse_text_report
    from alignment import PolicyAligner, AlignmentResult
    from models import (
        PolicyReport, PolicyParagraph, PolicyAlignment,
        ReportSource, ReportType, AlignmentMethod, POLICY_TOPICS
    )


# Initialize router
policy_router = APIRouter()

# Configuration
UPLOAD_DIR = Path("./uploads/policy")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Database path (same as Layer 1)
DB_PATH = Path("./corpus.db")

# Initialize components
db = PolicyDatabase(str(DB_PATH))
parser = PolicyPDFParser(output_dir="./parsed_policy")
aligner = PolicyAligner()


# ==================== Initialization ====================

@policy_router.on_event("startup")
async def startup():
    """Initialize Layer 2 database tables on startup."""
    await db.initialize()


# ==================== Report Endpoints ====================

@policy_router.post("/upload")
async def upload_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source: str = Form(..., description="Report source: pboc or fed"),
    title: str = Form(None, description="Report title (auto-detected if not provided)"),
    report_date: str = Form(None, description="Report date (YYYY-MM-DD)")
):
    """
    Upload and parse a policy report PDF.
    
    The report is processed in the background. Use GET /reports/{id} to check status.
    """
    # Validate source
    if source not in ["pboc", "fed"]:
        raise HTTPException(400, f"Invalid source: {source}. Must be 'pboc' or 'fed'")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    # Save uploaded file
    file_path = UPLOAD_DIR / f"{source}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Parse date if provided
    parsed_date = None
    if report_date:
        try:
            parsed_date = date.fromisoformat(report_date)
        except ValueError:
            raise HTTPException(400, f"Invalid date format: {report_date}. Use YYYY-MM-DD")
    
    # Parse PDF
    result = parser.parse(
        str(file_path),
        source=source,
        title=title,
        report_date=parsed_date
    )
    
    if not result.success:
        raise HTTPException(500, f"Failed to parse PDF: {result.error}")
    
    # Insert into database
    report_id = await db.insert_report(result.report)
    
    # Set report_id on paragraphs and insert
    for para in result.paragraphs:
        para.report_id = report_id
    await db.insert_paragraphs(report_id, result.paragraphs)
    
    return {
        "success": True,
        "report_id": report_id,
        "title": result.report.title,
        "date": str(result.report.report_date) if result.report.report_date else None,
        "paragraphs": len(result.paragraphs),
        "message": "Report uploaded and parsed successfully"
    }


@policy_router.post("/upload-text")
async def upload_text_report(request: dict):
    """
    Upload a policy report as plain text (no PDF required).
    Useful for testing or when PDF is already converted.
    
    Request body:
    {
        "text": "Report content...",
        "source": "pboc" or "fed",
        "title": "Report Title"
    }
    """
    text = request.get("text")
    source = request.get("source")
    title = request.get("title")
    
    if not text or not source or not title:
        raise HTTPException(400, "Missing required fields: text, source, title")
    
    if source not in ["pboc", "fed"]:
        raise HTTPException(400, f"Invalid source: {source}")
    
    result = parse_text_report(text, source=source, title=title)
    
    if not result.success:
        raise HTTPException(500, f"Failed to parse text: {result.error}")
    
    # Insert into database
    report_id = await db.insert_report(result.report)
    
    for para in result.paragraphs:
        para.report_id = report_id
    await db.insert_paragraphs(report_id, result.paragraphs)
    
    return {
        "success": True,
        "report": {"id": report_id, "title": result.report.title},
        "paragraphs_count": len(result.paragraphs)
    }


@policy_router.get("/reports")
async def list_reports(
    source: str = Query(None, description="Filter by source: pboc or fed"),
    report_type: str = Query(None, description="Filter by report type"),
    limit: int = Query(50, ge=1, le=200)
):
    """List all uploaded policy reports."""
    reports = await db.get_reports(source=source, report_type=report_type, limit=limit)
    return {
        "success": True,
        "total": len(reports),
        "reports": [r.to_dict() for r in reports]
    }


@policy_router.get("/reports/{report_id}")
async def get_report(report_id: int):
    """Get a specific report by ID."""
    report = await db.get_report(report_id)
    if not report:
        raise HTTPException(404, f"Report {report_id} not found")
    
    paragraphs = await db.get_paragraphs(report_id)
    
    return {
        "success": True,
        "report": report.to_dict(),
        "paragraphs": [p.to_dict() for p in paragraphs]
    }


@policy_router.delete("/reports/{report_id}")
async def delete_report(report_id: int):
    """Delete a report and all its paragraphs."""
    report = await db.get_report(report_id)
    if not report:
        raise HTTPException(404, f"Report {report_id} not found")
    
    await db.delete_report(report_id)
    
    return {
        "success": True,
        "message": f"Report {report_id} deleted"
    }


@policy_router.get("/reports/{report_id}/paragraphs")
async def get_paragraphs(
    report_id: int,
    topic: str = Query(None, description="Filter by topic")
):
    """Get paragraphs for a specific report."""
    paragraphs = await db.get_paragraphs(report_id, topic=topic)
    return {
        "success": True,
        "total": len(paragraphs),
        "paragraphs": [p.to_dict() for p in paragraphs]
    }


# ==================== Alignment Endpoints ====================

@policy_router.post("/align")
async def run_alignment(request: dict):
    """
    Run paragraph alignment between two reports.
    
    Request body:
    {
        "source_report_id": 1,
        "target_report_id": 2,
        "threshold": 0.5,
        "method": "auto",
        "topic_filter": null
    }
    """
    source_report_id = request.get("source_report_id")
    target_report_id = request.get("target_report_id")
    threshold = request.get("threshold", 0.5)
    method = request.get("method", "auto")
    topic_filter = request.get("topic_filter")
    
    if not source_report_id or not target_report_id:
        raise HTTPException(400, "Missing required fields: source_report_id, target_report_id")
    
    # Validate reports exist
    source_report = await db.get_report(source_report_id)
    target_report = await db.get_report(target_report_id)
    
    if not source_report:
        raise HTTPException(404, f"Source report {source_report_id} not found")
    if not target_report:
        raise HTTPException(404, f"Target report {target_report_id} not found")
    
    # Get paragraphs
    source_paragraphs = await db.get_paragraphs(source_report_id)
    target_paragraphs = await db.get_paragraphs(target_report_id)
    
    if not source_paragraphs or not target_paragraphs:
        raise HTTPException(400, "One or both reports have no paragraphs")
    
    # Run alignment
    result = aligner.align_reports(
        source_paragraphs,
        target_paragraphs,
        method=method,
        threshold=threshold,
        topic_filter=topic_filter
    )
    
    if not result.success:
        raise HTTPException(500, f"Alignment failed: {result.error}")
    
    # Store alignments in database
    if result.alignments:
        await db.insert_alignments(result.alignments)
    
    return {
        "success": True,
        "source_report": source_report.title,
        "target_report": target_report.title,
        "method": result.method.value,
        "threshold": threshold,
        "total_alignments": len(result.alignments),
        "alignments": [a.to_dict() for a in result.alignments[:20]]  # Return first 20
    }


@policy_router.get("/alignments")
async def get_alignments(
    source_report_id: int = Query(None),
    target_report_id: int = Query(None),
    topic: str = Query(None),
    term_id: int = Query(None, description="Filter by Layer 1 term ID"),
    min_similarity: float = Query(0.5),
    limit: int = Query(50, ge=1, le=200)
):
    """Get stored alignments with optional filtering."""
    alignments = await db.get_alignments(
        source_report_id=source_report_id,
        target_report_id=target_report_id,
        topic=topic,
        term_id=term_id,
        min_similarity=min_similarity,
        limit=limit
    )
    
    return {
        "success": True,
        "total": len(alignments),
        "alignments": [a.to_dict() for a in alignments]
    }


@policy_router.get("/alignments/term/{term}")
async def get_alignments_for_term(
    term: str,
    min_similarity: float = Query(0.5),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get alignments that mention a specific term.
    
    This endpoint links Layer 2 (policy) to Layer 1 (terminology).
    For example, searching for "Inflation" returns policy paragraph pairs
    that discuss inflation from both PBOC and Fed reports.
    """
    alignments = await db.get_alignments_for_term(
        term=term,
        min_similarity=min_similarity,
        limit=limit
    )
    
    return {
        "success": True,
        "term": term,
        "total": len(alignments),
        "alignments": [a.to_dict() for a in alignments]
    }


# ==================== Topic Endpoints ====================

@policy_router.get("/topics")
async def list_topics():
    """List available policy topics with their keywords."""
    topics = []
    for key, info in POLICY_TOPICS.items():
        topics.append({
            "key": key,
            "description": info["description"],
            "en_keywords": info["en_keywords"][:5],  # First 5
            "zh_keywords": info["zh_keywords"][:5]
        })
    return {
        "success": True,
        "topics": topics
    }


@policy_router.get("/topics/{topic}/paragraphs")
async def get_paragraphs_by_topic(
    topic: str,
    source: str = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """Get all paragraphs related to a specific topic."""
    if topic not in POLICY_TOPICS:
        raise HTTPException(400, f"Unknown topic: {topic}. Valid topics: {list(POLICY_TOPICS.keys())}")
    
    paragraphs = await db.get_paragraphs_by_topic(topic, source=source, limit=limit)
    
    return {
        "success": True,
        "topic": topic,
        "description": POLICY_TOPICS[topic]["description"],
        "total": len(paragraphs),
        "paragraphs": paragraphs
    }


# ==================== Statistics ====================

@policy_router.get("/stats")
async def get_statistics():
    """Get Layer 2 statistics."""
    stats = await db.get_statistics()
    return {
        "success": True,
        "layer": 2,
        "name": "Policy Parallel Corpus",
        "statistics": stats
    }


# ==================== Export ====================

@policy_router.get("/export")
async def export_alignments(
    format: str = Query("json", description="Export format: json or jsonl"),
    min_similarity: float = Query(0.5)
):
    """Export all alignments for dataset distribution."""
    alignments = await db.get_alignments(min_similarity=min_similarity, limit=10000)
    
    data = [a.to_dict() for a in alignments]
    
    if format == "jsonl":
        import json
        lines = [json.dumps(item, ensure_ascii=False) for item in data]
        content = "\n".join(lines)
        return JSONResponse(
            content={"data": content, "count": len(data)},
            headers={"Content-Disposition": "attachment; filename=policy_alignments.jsonl"}
        )
    else:
        return {
            "success": True,
            "format": "json",
            "total": len(data),
            "alignments": data
        }


# ==================== Integration with Layer 1 ====================

@policy_router.get("/search/{term}")
async def search_term_in_policy(
    term: str,
    include_alignments: bool = Query(True),
    limit: int = Query(10)
):
    """
    Search for a term across all policy reports.
    
    This is the main integration point with Layer 1 terminology.
    When a user searches for a term like "Inflation", this endpoint
    returns relevant policy paragraphs from both PBOC and Fed reports.
    """
    # Search in PBOC reports
    pboc_paragraphs = await db.get_paragraphs_by_topic(
        topic="inflation" if term.lower() == "inflation" else None,
        source="pboc",
        limit=limit
    )
    
    # Search in Fed reports
    fed_paragraphs = await db.get_paragraphs_by_topic(
        topic="inflation" if term.lower() == "inflation" else None,
        source="fed",
        limit=limit
    )
    
    result = {
        "success": True,
        "term": term,
        "pboc": {
            "total": len(pboc_paragraphs),
            "paragraphs": pboc_paragraphs[:5]
        },
        "fed": {
            "total": len(fed_paragraphs),
            "paragraphs": fed_paragraphs[:5]
        }
    }
    
    # Include alignments if requested
    if include_alignments:
        alignments = await db.get_alignments_for_term(term, limit=limit)
        result["alignments"] = {
            "total": len(alignments),
            "items": [a.to_dict() for a in alignments]
        }
    
    return result

# ==================== Export ====================

def clean_export_text(text):
    """Clean text for export by removing newlines and extra spaces."""
    if not text:
        return text
    import re
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

@policy_router.get("/export/alignments")
async def export_alignments(format: str = Query("jsonl", enum=["json", "jsonl"])):
    """Export all alignments in JSON or JSONL format."""
    import json
    from fastapi.responses import StreamingResponse
    
    alignments = await db.get_all_alignments()
    
    # Clean text in alignments
    for a in alignments:
        if a.source_text:
            a.source_text = clean_export_text(a.source_text)
        if a.target_text:
            a.target_text = clean_export_text(a.target_text)
    
    if format == "json":
        content = json.dumps({
            "total": len(alignments),
            "alignments": [a.to_dict() for a in alignments]
        }, indent=2, ensure_ascii=False)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=layer2_alignments.json"}
        )
    else:  # jsonl
        def generate():
            for a in alignments:
                yield json.dumps(a.to_dict(), ensure_ascii=False) + "\n"
        
        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",
            headers={"Content-Disposition": "attachment; filename=layer2_alignments.jsonl"}
        )


@policy_router.get("/export/reports")
async def export_reports(format: str = Query("jsonl", enum=["json", "jsonl"])):
    """Export all reports with paragraphs in JSON or JSONL format."""
    import json
    from fastapi.responses import StreamingResponse
    
    reports = await db.get_all_reports()
    
    # Fetch paragraphs for each report
    export_data = []
    for report in reports:
        paragraphs = await db.get_report_paragraphs(report.id)
        export_data.append({
            "report": report.to_dict(),
            "paragraphs": [p.to_dict() for p in paragraphs]
        })
    
    if format == "json":
        content = json.dumps({
            "total_reports": len(export_data),
            "reports": export_data
        }, indent=2, ensure_ascii=False)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=layer2_reports.json"}
        )
    else:  # jsonl
        def generate():
            for item in export_data:
                yield json.dumps(item, ensure_ascii=False) + "\n"
        
        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",
            headers={"Content-Disposition": "attachment; filename=layer2_reports.jsonl"}
        )


@policy_router.get("/export/parallel-corpus")
async def export_parallel_corpus(format: str = Query("jsonl", enum=["json", "jsonl", "tsv"])):
    """Export aligned paragraphs as parallel corpus for translation training."""
    import json
    from fastapi.responses import StreamingResponse
    
    alignments = await db.get_all_alignments()
    
    # Clean text in alignments
    for a in alignments:
        if a.source_text:
            a.source_text = clean_export_text(a.source_text)
        if a.target_text:
            a.target_text = clean_export_text(a.target_text)
    
    if format == "tsv":
        def generate():
            yield "source_text\ttarget_text\tsimilarity\ttopic\n"
            for a in alignments:
                source = (a.source_text or "").replace("\t", " ")
                target = (a.target_text or "").replace("\t", " ")
                yield f"{source}\t{target}\t{a.similarity_score:.3f}\t{a.topic or ''}\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/tab-separated-values",
            headers={"Content-Disposition": "attachment; filename=layer2_parallel_corpus.tsv"}
        )
    elif format == "json":
        corpus = [{
            "source": a.source_text,
            "target": a.target_text,
            "similarity": a.similarity_score,
            "topic": a.topic,
            "method": a.alignment_method.value if hasattr(a.alignment_method, 'value') else str(a.alignment_method)
        } for a in alignments]
        
        content = json.dumps({"pairs": corpus, "total": len(corpus)}, indent=2, ensure_ascii=False)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=layer2_parallel_corpus.json"}
        )
    else:  # jsonl
        def generate():
            for a in alignments:
                yield json.dumps({
                    "source": a.source_text,
                    "target": a.target_text,
                    "similarity": a.similarity_score,
                    "topic": a.topic
                }, ensure_ascii=False) + "\n"
        
        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",
            headers={"Content-Disposition": "attachment; filename=layer2_parallel_corpus.jsonl"}
        )


# ==================== Health Check ====================

@policy_router.get("/health")
async def health_check():
    """Health check for Layer 2 API."""
    stats = await db.get_statistics()
    return {
        "status": "healthy",
        "layer": 2,
        "name": "Policy Parallel Corpus",
        "reports": sum(stats.get("reports_by_source", {}).values()),
        "paragraphs": stats.get("total_paragraphs", 0),
        "alignments": stats.get("total_alignments", 0)
    }


# Create FastAPI application for standalone testing
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(
        title="EconMind Matrix - Layer 2 API",
        description="Policy Parallel Corpus API",
        version="1.0.0"
    )
    
    app.include_router(policy_router, prefix="/api/policy", tags=["policy"])
    
    @app.get("/")
    async def root():
        return {"message": "Layer 2 Policy API", "docs": "/docs"}
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
