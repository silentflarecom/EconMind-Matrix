"""
Data Loader for Layer 4

Loads data from Layer 1, 2, and 3 databases for alignment processing.
"""

import json
import aiosqlite
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Layer1Term:
    """Term data from Layer 1."""
    id: int
    term: str
    translations: Dict[str, Dict[str, str]]  # {lang: {summary, url}}
    depth_level: int = 0
    wikidata_qid: Optional[str] = None


@dataclass
class Layer2Paragraph:
    """Paragraph data from Layer 2."""
    id: int
    report_id: int
    text: str
    source: str  # 'pboc' or 'fed'
    topic: Optional[str] = None
    section_title: Optional[str] = None
    report_title: Optional[str] = None
    report_date: Optional[str] = None


@dataclass
class Layer3Article:
    """Article data from Layer 3."""
    id: int
    title: str
    summary: Optional[str]
    source: str
    url: str
    published_date: str
    sentiment_label: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    related_terms: List[str] = None
    
    def __post_init__(self):
        if self.related_terms is None:
            self.related_terms = []


class DataLoader:
    """
    Loads data from Layer 1-3 databases.
    
    All three layers share the same corpus.db file.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize DataLoader.
        
        Args:
            db_path: Path to corpus.db. Defaults to backend/corpus.db
        """
        if db_path is None:
            # Default path relative to project root
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "backend" / "corpus.db"
        
        self.db_path = str(db_path)
    
    async def load_layer1_terms(self, status: str = "completed") -> List[Layer1Term]:
        """
        Load all terms from Layer 1.
        
        Args:
            status: Filter by status (default: "completed")
            
        Returns:
            List of Layer1Term objects
        """
        terms = []
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = """
                SELECT id, term, translations, depth_level
                FROM terms
                WHERE status = ?
                ORDER BY id
            """
            
            cursor = await db.execute(query, (status,))
            rows = await cursor.fetchall()
            
            for row in rows:
                translations = {}
                if row['translations']:
                    try:
                        translations = json.loads(row['translations'])
                    except json.JSONDecodeError:
                        pass
                
                terms.append(Layer1Term(
                    id=row['id'],
                    term=row['term'],
                    translations=translations,
                    depth_level=row['depth_level'] or 0,
                    wikidata_qid=None  # TODO: Add wikidata_qid column
                ))
        
        return terms
    
    async def load_layer2_paragraphs(self) -> List[Layer2Paragraph]:
        """
        Load all policy paragraphs from Layer 2.
        
        Returns:
            List of Layer2Paragraph objects
        """
        paragraphs = []
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = """
                SELECT 
                    pp.id,
                    pp.report_id,
                    pp.paragraph_text as text,
                    pp.topic,
                    pp.section_title,
                    pr.source,
                    pr.title as report_title,
                    pr.report_date
                FROM policy_paragraphs pp
                JOIN policy_reports pr ON pp.report_id = pr.id
                ORDER BY pr.source, pr.report_date DESC, pp.id
            """
            
            try:
                cursor = await db.execute(query)
                rows = await cursor.fetchall()
                
                for row in rows:
                    paragraphs.append(Layer2Paragraph(
                        id=row['id'],
                        report_id=row['report_id'],
                        text=row['text'],
                        source=row['source'],
                        topic=row['topic'],
                        section_title=row['section_title'],
                        report_title=row['report_title'],
                        report_date=row['report_date']
                    ))
            except Exception as e:
                print(f"[WARN] Layer 2 tables not found or empty: {e}")
        
        return paragraphs
    
    async def load_layer3_articles(
        self, 
        days_back: int = 90,
        require_sentiment: bool = False
    ) -> List[Layer3Article]:
        """
        Load news articles from Layer 3.
        
        Args:
            days_back: Only load articles from last N days
            require_sentiment: If True, only load articles with sentiment annotations
            
        Returns:
            List of Layer3Article objects
        """
        articles = []
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if require_sentiment:
                query = """
                    SELECT 
                        na.id,
                        na.title,
                        na.summary,
                        na.source,
                        na.url,
                        na.published_date,
                        na.related_terms,
                        sa.sentiment_label,
                        sa.confidence_score
                    FROM news_articles na
                    JOIN sentiment_annotations sa ON na.id = sa.article_id
                    WHERE na.published_date >= ?
                    ORDER BY na.published_date DESC
                """
            else:
                query = """
                    SELECT 
                        na.id,
                        na.title,
                        na.summary,
                        na.source,
                        na.url,
                        na.published_date,
                        na.related_terms,
                        sa.sentiment_label,
                        sa.confidence_score
                    FROM news_articles na
                    LEFT JOIN sentiment_annotations sa ON na.id = sa.article_id
                    WHERE na.published_date >= ?
                    ORDER BY na.published_date DESC
                """
            
            try:
                cursor = await db.execute(query, (cutoff_date,))
                rows = await cursor.fetchall()
                
                for row in rows:
                    related_terms = []
                    if row['related_terms']:
                        try:
                            related_terms = json.loads(row['related_terms'])
                        except json.JSONDecodeError:
                            pass
                    
                    articles.append(Layer3Article(
                        id=row['id'],
                        title=row['title'],
                        summary=row['summary'],
                        source=row['source'],
                        url=row['url'],
                        published_date=row['published_date'] or "",
                        sentiment_label=row['sentiment_label'],
                        sentiment_confidence=row['confidence_score'],
                        related_terms=related_terms
                    ))
            except Exception as e:
                print(f"[WARN] Layer 3 tables not found or empty: {e}")
        
        return articles
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about available data.
        
        Returns:
            Dictionary with counts for each layer
        """
        stats = {
            "layer1": {"total_terms": 0, "completed_terms": 0},
            "layer2": {"total_reports": 0, "total_paragraphs": 0, "pboc_count": 0, "fed_count": 0},
            "layer3": {"total_articles": 0, "annotated_articles": 0, "sources": []}
        }
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Layer 1
            try:
                cursor = await db.execute("SELECT COUNT(*) as count FROM terms")
                row = await cursor.fetchone()
                stats["layer1"]["total_terms"] = row['count']
                
                cursor = await db.execute("SELECT COUNT(*) as count FROM terms WHERE status = 'completed'")
                row = await cursor.fetchone()
                stats["layer1"]["completed_terms"] = row['count']
            except:
                pass
            
            # Layer 2
            try:
                cursor = await db.execute("SELECT COUNT(*) as count FROM policy_reports")
                row = await cursor.fetchone()
                stats["layer2"]["total_reports"] = row['count']
                
                cursor = await db.execute("SELECT COUNT(*) as count FROM policy_paragraphs")
                row = await cursor.fetchone()
                stats["layer2"]["total_paragraphs"] = row['count']
                
                cursor = await db.execute("""
                    SELECT source, COUNT(*) as count 
                    FROM policy_reports 
                    GROUP BY source
                """)
                rows = await cursor.fetchall()
                for row in rows:
                    if row['source'] == 'pboc':
                        stats["layer2"]["pboc_count"] = row['count']
                    elif row['source'] == 'fed':
                        stats["layer2"]["fed_count"] = row['count']
            except:
                pass
            
            # Layer 3
            try:
                cursor = await db.execute("SELECT COUNT(*) as count FROM news_articles")
                row = await cursor.fetchone()
                stats["layer3"]["total_articles"] = row['count']
                
                cursor = await db.execute("""
                    SELECT COUNT(DISTINCT article_id) as count 
                    FROM sentiment_annotations
                """)
                row = await cursor.fetchone()
                stats["layer3"]["annotated_articles"] = row['count']
                
                cursor = await db.execute("SELECT DISTINCT source FROM news_articles LIMIT 20")
                rows = await cursor.fetchall()
                stats["layer3"]["sources"] = [row['source'] for row in rows]
            except:
                pass
        
        return stats
    
    async def search_paragraphs_for_term(
        self, 
        term: str, 
        term_variants: List[str] = None,
        limit: int = 50
    ) -> List[Layer2Paragraph]:
        """
        Search Layer 2 paragraphs that might be related to a term.
        
        Args:
            term: Primary term to search for
            term_variants: Additional term variants (e.g., translations)
            limit: Maximum number of results
            
        Returns:
            List of candidate paragraphs for alignment
        """
        if term_variants is None:
            term_variants = []
        
        all_variants = [term] + term_variants
        paragraphs = []
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Build LIKE conditions for all variants
            conditions = " OR ".join(["pp.paragraph_text LIKE ?" for _ in all_variants])
            params = [f"%{v}%" for v in all_variants]
            params.append(limit)
            
            query = f"""
                SELECT 
                    pp.id,
                    pp.report_id,
                    pp.paragraph_text as text,
                    pp.topic,
                    pp.section_title,
                    pr.source,
                    pr.title as report_title,
                    pr.report_date
                FROM policy_paragraphs pp
                JOIN policy_reports pr ON pp.report_id = pr.id
                WHERE {conditions}
                LIMIT ?
            """
            
            try:
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                for row in rows:
                    paragraphs.append(Layer2Paragraph(
                        id=row['id'],
                        report_id=row['report_id'],
                        text=row['text'],
                        source=row['source'],
                        topic=row['topic'],
                        section_title=row['section_title'],
                        report_title=row['report_title'],
                        report_date=row['report_date']
                    ))
            except Exception as e:
                print(f"[WARN] Error searching paragraphs: {e}")
        
        return paragraphs
    
    async def search_articles_for_term(
        self,
        term: str,
        term_variants: List[str] = None,
        days_back: int = 90,
        limit: int = 100
    ) -> List[Layer3Article]:
        """
        Search Layer 3 articles that might be related to a term.
        
        Args:
            term: Primary term to search for
            term_variants: Additional term variants
            days_back: Only search within last N days
            limit: Maximum number of results
            
        Returns:
            List of candidate articles for alignment
        """
        if term_variants is None:
            term_variants = []
        
        all_variants = [term] + term_variants
        articles = []
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Build conditions
            title_conditions = " OR ".join(["na.title LIKE ?" for _ in all_variants])
            summary_conditions = " OR ".join(["na.summary LIKE ?" for _ in all_variants])
            
            params = []
            params.extend([f"%{v}%" for v in all_variants])  # title
            params.extend([f"%{v}%" for v in all_variants])  # summary
            params.append(cutoff_date)
            params.append(limit)
            
            query = f"""
                SELECT 
                    na.id,
                    na.title,
                    na.summary,
                    na.source,
                    na.url,
                    na.published_date,
                    na.related_terms,
                    sa.sentiment_label,
                    sa.confidence_score
                FROM news_articles na
                LEFT JOIN sentiment_annotations sa ON na.id = sa.article_id
                WHERE ({title_conditions} OR {summary_conditions})
                AND na.published_date >= ?
                ORDER BY na.published_date DESC
                LIMIT ?
            """
            
            try:
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                for row in rows:
                    related_terms = []
                    if row['related_terms']:
                        try:
                            related_terms = json.loads(row['related_terms'])
                        except:
                            pass
                    
                    articles.append(Layer3Article(
                        id=row['id'],
                        title=row['title'],
                        summary=row['summary'],
                        source=row['source'],
                        url=row['url'],
                        published_date=row['published_date'] or "",
                        sentiment_label=row['sentiment_label'],
                        sentiment_confidence=row['confidence_score'],
                        related_terms=related_terms
                    ))
            except Exception as e:
                print(f"[WARN] Error searching articles: {e}")
        
        return articles
