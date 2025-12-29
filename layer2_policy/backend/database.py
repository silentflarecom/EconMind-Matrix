"""
Layer 2: Database Operations
Extends the Layer 1 database with policy report tables.

Usage:
    from database import PolicyDatabase
    
    db = PolicyDatabase("corpus.db")
    await db.initialize()
    report_id = await db.insert_report(report)
"""

import json
import aiosqlite
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import local models
try:
    from .models import (
        PolicyReport, PolicyParagraph, PolicyAlignment,
        ReportSource, ReportType, AlignmentMethod,
        LAYER2_SQL_SCHEMA
    )
except ImportError:
    from models import (
        PolicyReport, PolicyParagraph, PolicyAlignment,
        ReportSource, ReportType, AlignmentMethod,
        LAYER2_SQL_SCHEMA
    )


class PolicyDatabase:
    """
    Async database operations for Layer 2 policy data.
    Extends the existing Layer 1 corpus.db with policy tables.
    """
    
    def __init__(self, db_path: str = "corpus.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
    
    async def initialize(self):
        """Create Layer 2 tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(LAYER2_SQL_SCHEMA)
            await db.commit()
        print(f"Layer 2 database tables initialized in {self.db_path}")
    
    # ==================== Report Operations ====================
    
    async def insert_report(self, report: PolicyReport) -> int:
        """
        Insert a new policy report.
        
        Args:
            report: PolicyReport object
            
        Returns:
            Inserted report ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO policy_reports 
                   (source, report_type, title, report_date, raw_text, 
                    parsed_markdown, file_path, language)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    report.source.value,
                    report.report_type.value,
                    report.title,
                    report.report_date.isoformat() if report.report_date else None,
                    report.raw_text,
                    report.parsed_markdown,
                    report.file_path,
                    report.language
                )
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_report(self, report_id: int) -> Optional[PolicyReport]:
        """Get a report by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM policy_reports WHERE id = ?",
                (report_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_report(row)
        return None
    
    async def get_reports(
        self,
        source: str = None,
        report_type: str = None,
        limit: int = 100
    ) -> List[PolicyReport]:
        """
        Get all reports with optional filtering.
        
        Args:
            source: Filter by source ("pboc", "fed")
            report_type: Filter by report type
            limit: Maximum results
            
        Returns:
            List of PolicyReport objects
        """
        conditions = []
        params = []
        
        if source:
            conditions.append("source = ?")
            params.append(source)
        if report_type:
            conditions.append("report_type = ?")
            params.append(report_type)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                f"""SELECT * FROM policy_reports 
                    WHERE {where_clause}
                    ORDER BY report_date DESC
                    LIMIT ?""",
                (*params, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_report(row) for row in rows]
    
    async def delete_report(self, report_id: int) -> bool:
        """Delete a report and its paragraphs (cascade)."""
        async with aiosqlite.connect(self.db_path) as db:
            # Enable foreign keys for cascade delete
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute(
                "DELETE FROM policy_reports WHERE id = ?",
                (report_id,)
            )
            await db.commit()
            return True
    
    def _row_to_report(self, row: aiosqlite.Row) -> PolicyReport:
        """Convert database row to PolicyReport object."""
        from datetime import date
        
        report_date = None
        if row['report_date']:
            try:
                report_date = date.fromisoformat(row['report_date'])
            except:
                pass
        
        return PolicyReport(
            id=row['id'],
            source=ReportSource(row['source']),
            report_type=ReportType(row['report_type']),
            title=row['title'],
            report_date=report_date,
            raw_text=row['raw_text'] or "",
            parsed_markdown=row['parsed_markdown'] or "",
            file_path=row['file_path'],
            language=row['language'] or "zh",
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
    
    # ==================== Paragraph Operations ====================
    
    async def insert_paragraphs(
        self,
        report_id: int,
        paragraphs: List[PolicyParagraph]
    ) -> List[int]:
        """
        Insert multiple paragraphs for a report.
        
        Args:
            report_id: Parent report ID
            paragraphs: List of PolicyParagraph objects
            
        Returns:
            List of inserted paragraph IDs
        """
        async with aiosqlite.connect(self.db_path) as db:
            ids = []
            for para in paragraphs:
                cursor = await db.execute(
                    """INSERT INTO policy_paragraphs
                       (report_id, paragraph_index, paragraph_text, topic,
                        topic_confidence, section_title, word_count, embedding)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        report_id,
                        para.paragraph_index,
                        para.paragraph_text,
                        para.topic,
                        para.topic_confidence,
                        para.section_title,
                        para.word_count,
                        para.embedding
                    )
                )
                ids.append(cursor.lastrowid)
            await db.commit()
            return ids
    
    async def get_paragraphs(
        self,
        report_id: int,
        topic: str = None
    ) -> List[PolicyParagraph]:
        """
        Get paragraphs for a report.
        
        Args:
            report_id: Report ID
            topic: Optional topic filter
            
        Returns:
            List of PolicyParagraph objects
        """
        conditions = ["report_id = ?"]
        params = [report_id]
        
        if topic:
            conditions.append("topic = ?")
            params.append(topic)
        
        where_clause = " AND ".join(conditions)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                f"""SELECT * FROM policy_paragraphs 
                    WHERE {where_clause}
                    ORDER BY paragraph_index""",
                params
            ) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_paragraph(row) for row in rows]
    
    async def get_paragraphs_by_topic(
        self,
        topic: str,
        source: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get paragraphs by topic across all reports.
        
        Args:
            topic: Topic to filter by
            source: Optional source filter ("pboc", "fed")
            limit: Maximum results
            
        Returns:
            List of paragraph dicts with report info
        """
        query = """
            SELECT p.*, r.source, r.title as report_title, r.report_date
            FROM policy_paragraphs p
            JOIN policy_reports r ON p.report_id = r.id
            WHERE p.topic = ?
        """
        params = [topic]
        
        if source:
            query += " AND r.source = ?"
            params.append(source)
        
        query += f" ORDER BY p.topic_confidence DESC LIMIT {limit}"
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    def _row_to_paragraph(self, row: aiosqlite.Row) -> PolicyParagraph:
        """Convert database row to PolicyParagraph object."""
        return PolicyParagraph(
            id=row['id'],
            report_id=row['report_id'],
            paragraph_index=row['paragraph_index'],
            paragraph_text=row['paragraph_text'],
            topic=row['topic'],
            topic_confidence=row['topic_confidence'] or 0.0,
            section_title=row['section_title'],
            word_count=row['word_count'] or 0,
            embedding=row['embedding'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
    
    # ==================== Alignment Operations ====================
    
    async def insert_alignments(
        self,
        alignments: List[PolicyAlignment]
    ) -> List[int]:
        """
        Insert multiple alignments.
        
        Args:
            alignments: List of PolicyAlignment objects
            
        Returns:
            List of inserted alignment IDs
        """
        async with aiosqlite.connect(self.db_path) as db:
            ids = []
            for a in alignments:
                cursor = await db.execute(
                    """INSERT INTO policy_alignments
                       (source_paragraph_id, target_paragraph_id, similarity_score,
                        alignment_method, topic, term_id, verified)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        a.source_paragraph_id,
                        a.target_paragraph_id,
                        a.similarity_score,
                        a.alignment_method.value,
                        a.topic,
                        a.term_id,
                        a.verified
                    )
                )
                ids.append(cursor.lastrowid)
            await db.commit()
            return ids
    
    async def get_alignments(
        self,
        source_report_id: int = None,
        target_report_id: int = None,
        topic: str = None,
        term_id: int = None,
        min_similarity: float = 0.0,
        limit: int = 100
    ) -> List[PolicyAlignment]:
        """
        Get alignments with optional filtering.
        
        Args:
            source_report_id: Filter by source report
            target_report_id: Filter by target report
            topic: Filter by topic
            term_id: Filter by related term (Layer 1)
            min_similarity: Minimum similarity score
            limit: Maximum results
            
        Returns:
            List of PolicyAlignment objects with paragraph texts
        """
        query = """
            SELECT 
                a.*,
                sp.paragraph_text as source_text,
                tp.paragraph_text as target_text,
                sr.title as source_report_title,
                tr.title as target_report_title
            FROM policy_alignments a
            JOIN policy_paragraphs sp ON a.source_paragraph_id = sp.id
            JOIN policy_paragraphs tp ON a.target_paragraph_id = tp.id
            JOIN policy_reports sr ON sp.report_id = sr.id
            JOIN policy_reports tr ON tp.report_id = tr.id
            WHERE a.similarity_score >= ?
        """
        params = [min_similarity]
        
        if source_report_id:
            query += " AND sp.report_id = ?"
            params.append(source_report_id)
        if target_report_id:
            query += " AND tp.report_id = ?"
            params.append(target_report_id)
        if topic:
            query += " AND a.topic = ?"
            params.append(topic)
        if term_id:
            query += " AND a.term_id = ?"
            params.append(term_id)
        
        query += f" ORDER BY a.similarity_score DESC LIMIT {limit}"
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_alignment(row) for row in rows]
    
    async def get_alignments_for_term(
        self,
        term: str,
        min_similarity: float = 0.5,
        limit: int = 10
    ) -> List[PolicyAlignment]:
        """
        Get alignments that mention a specific term.
        
        Args:
            term: Term to search (e.g., "Inflation")
            min_similarity: Minimum similarity score
            limit: Maximum results
            
        Returns:
            List of PolicyAlignment objects
        """
        # Search in both source and target paragraph texts
        search_term = f"%{term}%"
        
        query = """
            SELECT 
                a.*,
                sp.paragraph_text as source_text,
                tp.paragraph_text as target_text,
                sr.title as source_report_title,
                tr.title as target_report_title
            FROM policy_alignments a
            JOIN policy_paragraphs sp ON a.source_paragraph_id = sp.id
            JOIN policy_paragraphs tp ON a.target_paragraph_id = tp.id
            JOIN policy_reports sr ON sp.report_id = sr.id
            JOIN policy_reports tr ON tp.report_id = tr.id
            WHERE a.similarity_score >= ?
            AND (sp.paragraph_text LIKE ? OR tp.paragraph_text LIKE ?)
            ORDER BY a.similarity_score DESC
            LIMIT ?
        """
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, (min_similarity, search_term, search_term, limit)) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_alignment(row) for row in rows]
    
    def _row_to_alignment(self, row: aiosqlite.Row) -> PolicyAlignment:
        """Convert database row to PolicyAlignment object."""
        # Convert to dict for easier access
        row_dict = dict(row)
        
        # Handle alignment_method conversion with fallback
        try:
            method = AlignmentMethod(row_dict.get('alignment_method', 'keyword_matching'))
        except (ValueError, KeyError):
            method = AlignmentMethod.KEYWORD_MATCHING
        
        return PolicyAlignment(
            id=row_dict.get('id'),
            source_paragraph_id=row_dict.get('source_paragraph_id', 0),
            target_paragraph_id=row_dict.get('target_paragraph_id', 0),
            similarity_score=row_dict.get('similarity_score', 0.0),
            alignment_method=method,
            topic=row_dict.get('topic'),
            term_id=row_dict.get('term_id'),
            verified=bool(row_dict.get('verified')) if row_dict.get('verified') else False,
            source_text=row_dict.get('source_text'),
            target_text=row_dict.get('target_text'),
            source_report_title=row_dict.get('source_report_title'),
            target_report_title=row_dict.get('target_report_title'),
            created_at=datetime.fromisoformat(row_dict['created_at']) if row_dict.get('created_at') else None
        )
    
    # ==================== Statistics ====================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get Layer 2 statistics."""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Report counts by source
            async with db.execute(
                "SELECT source, COUNT(*) FROM policy_reports GROUP BY source"
            ) as cursor:
                rows = await cursor.fetchall()
                stats["reports_by_source"] = {row[0]: row[1] for row in rows}
            
            # Total paragraphs
            async with db.execute(
                "SELECT COUNT(*) FROM policy_paragraphs"
            ) as cursor:
                stats["total_paragraphs"] = (await cursor.fetchone())[0]
            
            # Paragraphs by topic
            async with db.execute(
                """SELECT topic, COUNT(*) FROM policy_paragraphs 
                   WHERE topic IS NOT NULL GROUP BY topic"""
            ) as cursor:
                rows = await cursor.fetchall()
                stats["paragraphs_by_topic"] = {row[0]: row[1] for row in rows}
            
            # Total alignments
            async with db.execute(
                "SELECT COUNT(*) FROM policy_alignments"
            ) as cursor:
                stats["total_alignments"] = (await cursor.fetchone())[0]
            
            # Average similarity score
            async with db.execute(
                "SELECT AVG(similarity_score) FROM policy_alignments"
            ) as cursor:
                avg = (await cursor.fetchone())[0]
                stats["avg_similarity"] = round(avg, 4) if avg else 0
            
            return stats
    
    # ==================== Export Helpers ====================
    
    async def get_all_reports(self) -> List[PolicyReport]:
        """Get all reports for export."""
        return await self.get_reports(limit=10000)
    
    async def get_all_alignments(self) -> List[PolicyAlignment]:
        """Get all alignments for export."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT 
                    a.*,
                    sp.paragraph_text as source_text,
                    tp.paragraph_text as target_text,
                    sr.title as source_report_title,
                    tr.title as target_report_title
                FROM policy_alignments a
                LEFT JOIN policy_paragraphs sp ON a.source_paragraph_id = sp.id
                LEFT JOIN policy_paragraphs tp ON a.target_paragraph_id = tp.id
                LEFT JOIN policy_reports sr ON sp.report_id = sr.id
                LEFT JOIN policy_reports tr ON tp.report_id = tr.id
                ORDER BY a.similarity_score DESC
            """) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_alignment(row) for row in rows]
    
    async def get_report_paragraphs(self, report_id: int) -> List[PolicyParagraph]:
        """Get all paragraphs for a specific report."""
        return await self.get_paragraphs(report_id)


# Convenience function for quick database initialization
async def init_layer2_database(db_path: str = "corpus.db"):
    """Initialize Layer 2 database tables."""
    db = PolicyDatabase(db_path)
    await db.initialize()
    return db


if __name__ == "__main__":
    import asyncio
    
    async def test_database():
        print("Testing Layer 2 Database")
        print("=" * 60)
        
        # Initialize database
        db = PolicyDatabase("test_layer2.db")
        await db.initialize()
        print("Database initialized.")
        
        # Create test report
        from models import PolicyReport, ReportSource, ReportType
        from datetime import date
        
        report = PolicyReport(
            source=ReportSource.PBOC,
            report_type=ReportType.MONETARY_POLICY,
            title="Test Report 2024Q3",
            report_date=date(2024, 9, 30),
            parsed_markdown="# Test Report\n\nTest content here.",
            language="zh"
        )
        
        # Insert report
        report_id = await db.insert_report(report)
        print(f"Inserted report ID: {report_id}")
        
        # Insert paragraphs
        from models import PolicyParagraph
        paragraphs = [
            PolicyParagraph(paragraph_index=0, paragraph_text="通胀水平保持温和。", topic="inflation"),
            PolicyParagraph(paragraph_index=1, paragraph_text="就业形势总体稳定。", topic="employment"),
        ]
        para_ids = await db.insert_paragraphs(report_id, paragraphs)
        print(f"Inserted paragraph IDs: {para_ids}")
        
        # Get report
        fetched = await db.get_report(report_id)
        print(f"Fetched report: {fetched.title}")
        
        # Get paragraphs
        paras = await db.get_paragraphs(report_id)
        print(f"Fetched {len(paras)} paragraphs")
        
        # Get statistics
        stats = await db.get_statistics()
        print(f"Statistics: {stats}")
        
        print("\nTest complete!")
    
    asyncio.run(test_database())
