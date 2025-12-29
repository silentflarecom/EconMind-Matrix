"""
Centralized Database Schema Definitions for EconMind-Matrix

This module contains all SQL schema definitions for the three layers:
- Layer 1: Terminology Corpus (batch_tasks, terms, term_associations, system_settings)
- Layer 2: Policy Parallel Corpus (policy_reports, policy_paragraphs, policy_alignments)
- Layer 3: Sentiment Corpus (news_articles, sentiment_annotations, market_context, term_frequency)

Created as part of Technical Debt Issue #6 fix.

Usage:
    from shared.schema import LAYER1_SQL_SCHEMA, LAYER2_SQL_SCHEMA, LAYER3_SQL_SCHEMA, ALL_SCHEMAS

    # Initialize all tables
    for schema in ALL_SCHEMAS.values():
        for statement in schema.split(';'):
            if statement.strip():
                await db.execute(statement)
"""

from typing import Dict

# =============================================================================
# Layer 1: Terminology Corpus Schema
# =============================================================================

LAYER1_SQL_SCHEMA = """
-- Batch tasks table
CREATE TABLE IF NOT EXISTS batch_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_terms INTEGER NOT NULL,
    completed_terms INTEGER DEFAULT 0,
    failed_terms INTEGER DEFAULT 0,
    crawl_interval INTEGER DEFAULT 3,
    max_depth INTEGER DEFAULT 1,
    target_languages TEXT DEFAULT 'en,zh'
);

-- Terms table
CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    term TEXT NOT NULL,
    status TEXT NOT NULL,
    en_summary TEXT,
    en_url TEXT,
    zh_summary TEXT,
    zh_url TEXT,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    depth_level INTEGER DEFAULT 0,
    source_term_id INTEGER,
    translations TEXT,  -- JSON: {"lang": {"summary": "...", "url": "..."}}
    FOREIGN KEY (task_id) REFERENCES batch_tasks(id)
);

-- Term associations table
CREATE TABLE IF NOT EXISTS term_associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_term_id INTEGER,
    target_term TEXT,
    association_type TEXT,
    weight REAL DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_term_id) REFERENCES terms(id)
);

-- System settings table
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Layer 1 indexes
CREATE INDEX IF NOT EXISTS idx_terms_task ON terms(task_id);
CREATE INDEX IF NOT EXISTS idx_terms_status ON terms(status);
CREATE INDEX IF NOT EXISTS idx_terms_term ON terms(term);
CREATE INDEX IF NOT EXISTS idx_associations_source ON term_associations(source_term_id);
"""

# Default values for Layer 1
LAYER1_DEFAULTS = {
    "user_agent": "TermCorpusBot/1.0 (Educational Project; mailto:your-email@example.com)"
}


# =============================================================================
# Layer 2: Policy Parallel Corpus Schema
# =============================================================================

LAYER2_SQL_SCHEMA = """
-- Policy reports table
CREATE TABLE IF NOT EXISTS policy_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    report_type TEXT NOT NULL,
    title TEXT NOT NULL,
    report_date DATE,
    raw_text TEXT,
    parsed_markdown TEXT,
    file_path TEXT,
    language TEXT DEFAULT 'zh',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Policy paragraphs table
CREATE TABLE IF NOT EXISTS policy_paragraphs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    paragraph_index INTEGER NOT NULL,
    paragraph_text TEXT NOT NULL,
    topic TEXT,
    topic_confidence REAL DEFAULT 0.0,
    section_title TEXT,
    word_count INTEGER DEFAULT 0,
    embedding BLOB,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES policy_reports(id) ON DELETE CASCADE
);

-- Policy alignments table
CREATE TABLE IF NOT EXISTS policy_alignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_paragraph_id INTEGER NOT NULL,
    target_paragraph_id INTEGER NOT NULL,
    similarity_score REAL NOT NULL,
    alignment_method TEXT DEFAULT 'sentence_bert',
    topic TEXT,
    term_id INTEGER,
    verified BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_paragraph_id) REFERENCES policy_paragraphs(id) ON DELETE CASCADE,
    FOREIGN KEY (target_paragraph_id) REFERENCES policy_paragraphs(id) ON DELETE CASCADE,
    FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE SET NULL
);

-- Layer 2 indexes
CREATE INDEX IF NOT EXISTS idx_paragraphs_report ON policy_paragraphs(report_id);
CREATE INDEX IF NOT EXISTS idx_paragraphs_topic ON policy_paragraphs(topic);
CREATE INDEX IF NOT EXISTS idx_alignments_similarity ON policy_alignments(similarity_score DESC);
CREATE INDEX IF NOT EXISTS idx_alignments_topic ON policy_alignments(topic);
CREATE INDEX IF NOT EXISTS idx_alignments_term ON policy_alignments(term_id);
"""


# =============================================================================
# Layer 3: Sentiment Corpus Schema
# =============================================================================

LAYER3_SQL_SCHEMA = """
-- News articles table
CREATE TABLE IF NOT EXISTS news_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    published_date DATETIME,
    summary TEXT,
    full_text TEXT,
    language TEXT DEFAULT 'en',
    related_terms TEXT,  -- JSON array of term strings
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Sentiment annotations table
CREATE TABLE IF NOT EXISTS sentiment_annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    sentiment_label TEXT NOT NULL,
    confidence_score REAL DEFAULT 0.0,
    annotation_source TEXT NOT NULL,
    reasoning TEXT,
    detected_entities TEXT,  -- JSON array of entities
    verified BOOLEAN DEFAULT FALSE,
    verified_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES news_articles(id) ON DELETE CASCADE
);

-- Market context table
CREATE TABLE IF NOT EXISTS market_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    context_date DATE UNIQUE NOT NULL,
    sp500_close REAL,
    sp500_change_pct REAL,
    nasdaq_close REAL,
    nasdaq_change_pct REAL,
    vix_close REAL,
    us_10y_yield REAL,
    dxy_close REAL,
    sse_close REAL,
    sse_change_pct REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Term frequency history (for trend analysis)
CREATE TABLE IF NOT EXISTS term_frequency (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL,
    frequency_date DATE NOT NULL,
    mention_count INTEGER DEFAULT 0,
    bullish_count INTEGER DEFAULT 0,
    bearish_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    avg_sentiment REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(term, frequency_date)
);

-- Layer 3 indexes
CREATE INDEX IF NOT EXISTS idx_articles_source ON news_articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_date ON news_articles(published_date DESC);
CREATE INDEX IF NOT EXISTS idx_articles_language ON news_articles(language);
CREATE INDEX IF NOT EXISTS idx_annotations_article ON sentiment_annotations(article_id);
CREATE INDEX IF NOT EXISTS idx_annotations_sentiment ON sentiment_annotations(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_annotations_source ON sentiment_annotations(annotation_source);
CREATE INDEX IF NOT EXISTS idx_market_date ON market_context(context_date);
CREATE INDEX IF NOT EXISTS idx_frequency_term ON term_frequency(term, frequency_date);
"""


# =============================================================================
# Combined Schemas
# =============================================================================

ALL_SCHEMAS: Dict[str, str] = {
    "layer1": LAYER1_SQL_SCHEMA,
    "layer2": LAYER2_SQL_SCHEMA,
    "layer3": LAYER3_SQL_SCHEMA,
}


# Table names by layer for reference
LAYER1_TABLES = ["batch_tasks", "terms", "term_associations", "system_settings"]
LAYER2_TABLES = ["policy_reports", "policy_paragraphs", "policy_alignments"]
LAYER3_TABLES = ["news_articles", "sentiment_annotations", "market_context", "term_frequency"]
ALL_TABLES = LAYER1_TABLES + LAYER2_TABLES + LAYER3_TABLES


def get_all_table_drop_statements() -> str:
    """Generate DROP TABLE statements for all tables (for reset functionality)."""
    statements = []
    for table in reversed(ALL_TABLES):  # Reverse to handle foreign key dependencies
        statements.append(f"DROP TABLE IF EXISTS {table}")
    return ";\n".join(statements) + ";"


def get_schema_version() -> str:
    """Get current schema version for migration tracking."""
    return "1.0.0"
