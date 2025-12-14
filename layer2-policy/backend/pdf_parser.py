"""
Layer 2: PDF Parser Module
Parses policy report PDFs into structured Markdown using Marker.

Supports:
- PBOC Monetary Policy Execution Reports
- Fed Beige Book
- Fed FOMC Minutes

Usage:
    from pdf_parser import PolicyPDFParser
    
    parser = PolicyPDFParser()
    result = parser.parse("path/to/report.pdf", source="pboc")
    print(result.parsed_markdown)
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import date
from dataclasses import dataclass

# Try to import Marker
try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False
    print("Warning: Marker not installed. Install with: pip install marker-pdf")

# Import local models
try:
    from .models import PolicyReport, PolicyParagraph, ReportSource, ReportType, get_topic_by_keywords
except ImportError:
    from models import PolicyReport, PolicyParagraph, ReportSource, ReportType, get_topic_by_keywords


@dataclass
class ParseResult:
    """Result of parsing a PDF file."""
    success: bool
    report: Optional[PolicyReport] = None
    paragraphs: List[PolicyParagraph] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.paragraphs is None:
            self.paragraphs = []


class PolicyPDFParser:
    """
    Parser for policy report PDFs.
    Uses Marker for PDF to Markdown conversion.
    """
    
    # Minimum paragraph length (characters) to include
    MIN_PARAGRAPH_LENGTH = 50
    
    # Section patterns for different report types
    SECTION_PATTERNS = {
        "pboc": [
            r"^第[一二三四五六七八九十]+[部分章节]",
            r"^[一二三四五六七八九十]+[、．.]",
            r"^（[一二三四五六七八九十]+）",
            r"^专栏\s*\d+",
        ],
        "fed": [
            r"^(?:National|District|Summary|Federal Open Market)",
            r"^(?:Consumer Spending|Manufacturing|Employment|Prices)",
            r"^(?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|Eleventh|Twelfth) District",
        ]
    }
    
    def __init__(self, output_dir: str = None):
        """
        Initialize the parser.
        
        Args:
            output_dir: Directory to save parsed Markdown files
        """
        self.output_dir = Path(output_dir) if output_dir else Path("./parsed_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._marker_models = None
    
    def _init_marker(self):
        """Initialize Marker models (lazy loading)."""
        if not MARKER_AVAILABLE:
            raise RuntimeError(
                "Marker is not installed. Please install with:\n"
                "  pip install marker-pdf\n"
                "Note: This requires PyTorch and may need GPU for best performance."
            )
        
        if self._marker_models is None:
            print("Loading Marker models... (this may take a moment)")
            self._marker_models = create_model_dict()
            print("Marker models loaded.")
    
    def parse(
        self,
        pdf_path: str,
        source: str = "pboc",
        title: str = None,
        report_date: date = None
    ) -> ParseResult:
        """
        Parse a PDF file into structured data.
        
        Args:
            pdf_path: Path to the PDF file
            source: Report source ("pboc" or "fed")
            title: Report title (auto-detected if not provided)
            report_date: Report date (auto-detected if not provided)
            
        Returns:
            ParseResult with report and paragraphs
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            return ParseResult(success=False, error=f"File not found: {pdf_path}")
        
        try:
            # Convert PDF to Markdown using Marker
            markdown_text = self._convert_pdf_to_markdown(pdf_path)
            
            # Extract title if not provided
            if not title:
                title = self._extract_title(markdown_text, source)
            
            # Extract date if not provided
            if not report_date:
                report_date = self._extract_date(markdown_text, source)
            
            # Determine report type
            report_type = self._detect_report_type(title, source)
            
            # Create PolicyReport object
            report = PolicyReport(
                source=ReportSource(source),
                report_type=report_type,
                title=title or pdf_path.stem,
                report_date=report_date,
                parsed_markdown=markdown_text,
                file_path=str(pdf_path.absolute()),
                language="zh" if source == "pboc" else "en"
            )
            
            # Split into paragraphs
            paragraphs = self._split_paragraphs(markdown_text, source)
            
            # Save Markdown file
            output_file = self.output_dir / f"{pdf_path.stem}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            
            return ParseResult(
                success=True,
                report=report,
                paragraphs=paragraphs
            )
            
        except Exception as e:
            return ParseResult(success=False, error=str(e))
    
    def _convert_pdf_to_markdown(self, pdf_path: Path) -> str:
        """
        Convert PDF to Markdown using Marker.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Markdown text
        """
        if MARKER_AVAILABLE:
            self._init_marker()
            
            # Use Marker to convert
            converter = PdfConverter(artifact_dict=self._marker_models)
            rendered = converter(str(pdf_path))
            markdown_text = text_from_rendered(rendered)
            return markdown_text
        else:
            # Fallback: Use PyPDF2 for basic text extraction
            return self._fallback_pdf_extract(pdf_path)
    
    def _fallback_pdf_extract(self, pdf_path: Path) -> str:
        """
        Fallback PDF extraction using PyPDF2.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text (less structured than Marker)
        """
        try:
            import PyPDF2
        except ImportError:
            raise RuntimeError(
                "Neither Marker nor PyPDF2 is installed.\n"
                "Install one of:\n"
                "  pip install marker-pdf  (recommended)\n"
                "  pip install PyPDF2  (basic fallback)"
            )
        
        text_parts = []
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    def _extract_title(self, markdown: str, source: str) -> Optional[str]:
        """Extract report title from Markdown content."""
        lines = markdown.split('\n')
        
        if source == "pboc":
            # Look for "货币政策执行报告" or similar
            for line in lines[:20]:
                if "货币政策" in line and "报告" in line:
                    return line.strip().strip('#').strip()
                if "执行报告" in line:
                    return line.strip().strip('#').strip()
        else:
            # Look for common Fed report titles
            for line in lines[:20]:
                line_clean = line.strip().strip('#').strip()
                if "Beige Book" in line_clean:
                    return line_clean
                if "FOMC" in line_clean:
                    return line_clean
                if "Federal Reserve" in line_clean:
                    return line_clean
        
        # Return first non-empty line as fallback
        for line in lines[:10]:
            line_clean = line.strip().strip('#').strip()
            if len(line_clean) > 10:
                return line_clean
        
        return None
    
    def _extract_date(self, markdown: str, source: str) -> Optional[date]:
        """Extract report date from Markdown content."""
        import re
        from datetime import datetime
        
        text = markdown[:2000]  # Only search first part
        
        if source == "pboc":
            # Look for patterns like "2024年第三季度" or "二○二四年"
            patterns = [
                r'(\d{4})年[第]?([一二三四1234])季度',
                r'(\d{4})年(\d{1,2})月',
                r'二[○〇零0]([一二三四五六七八九零〇\d]{2})年',
            ]
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        year = int(match.group(1))
                        return date(year, 12, 31)  # Use end of year as approximate
                    except:
                        continue
        else:
            # Look for patterns like "December 2024" or "2024-12-04"
            patterns = [
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
                r'(\d{4})-(\d{2})-(\d{2})',
            ]
            months = {
                'January': 1, 'February': 2, 'March': 3, 'April': 4,
                'May': 5, 'June': 6, 'July': 7, 'August': 8,
                'September': 9, 'October': 10, 'November': 11, 'December': 12
            }
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        if match.group(1) in months:
                            return date(int(match.group(2)), months[match.group(1)], 1)
                        else:
                            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                    except:
                        continue
        
        return None
    
    def _detect_report_type(self, title: str, source: str) -> ReportType:
        """Detect report type from title."""
        if not title:
            return ReportType.MONETARY_POLICY
        
        title_lower = title.lower()
        
        if source == "pboc":
            if "货币政策" in title:
                return ReportType.MONETARY_POLICY
            if "金融稳定" in title:
                return ReportType.FINANCIAL_STABILITY
        else:
            if "beige book" in title_lower:
                return ReportType.BEIGE_BOOK
            if "fomc" in title_lower and "minute" in title_lower:
                return ReportType.FOMC_MINUTES
            if "fomc" in title_lower and "statement" in title_lower:
                return ReportType.FOMC_STATEMENT
        
        return ReportType.MONETARY_POLICY
    
    def _split_paragraphs(
        self,
        markdown: str,
        source: str
    ) -> List[PolicyParagraph]:
        """
        Split Markdown into paragraphs with topic detection.
        
        Args:
            markdown: Markdown text
            source: Report source for section pattern matching
            
        Returns:
            List of PolicyParagraph objects
        """
        # Split by double newlines (standard paragraph separation)
        raw_paragraphs = re.split(r'\n\s*\n', markdown)
        
        # Get section patterns for this source
        section_patterns = self.SECTION_PATTERNS.get(source, [])
        section_regex = '|'.join(section_patterns) if section_patterns else None
        
        paragraphs = []
        current_section = None
        
        for idx, para_text in enumerate(raw_paragraphs):
            para_text = para_text.strip()
            
            # Skip empty or too short paragraphs
            if len(para_text) < self.MIN_PARAGRAPH_LENGTH:
                # But check if it's a section header
                if section_regex and re.match(section_regex, para_text, re.MULTILINE):
                    current_section = para_text.strip('#').strip()
                continue
            
            # Skip if it looks like a table or figure caption
            if para_text.startswith('|') or para_text.startswith('图') or para_text.startswith('表'):
                continue
            
            # Detect topic
            language = "zh" if source == "pboc" else "en"
            topic, confidence = get_topic_by_keywords(para_text, language)
            
            paragraph = PolicyParagraph(
                paragraph_index=len(paragraphs),
                paragraph_text=para_text,
                topic=topic,
                topic_confidence=confidence,
                section_title=current_section
            )
            paragraphs.append(paragraph)
        
        return paragraphs
    
    def parse_pboc_report(self, pdf_path: str, title: str = None, report_date: date = None) -> ParseResult:
        """Convenience method for parsing PBOC reports."""
        return self.parse(pdf_path, source="pboc", title=title, report_date=report_date)
    
    def parse_fed_report(self, pdf_path: str, title: str = None, report_date: date = None) -> ParseResult:
        """Convenience method for parsing Fed reports."""
        return self.parse(pdf_path, source="fed", title=title, report_date=report_date)


def parse_text_report(text: str, source: str = "pboc", title: str = "Manual Input") -> ParseResult:
    """
    Parse a report from raw text (no PDF).
    Useful for testing or when PDF is already converted.
    
    Args:
        text: Report text content
        source: Report source ("pboc" or "fed")
        title: Report title
        
    Returns:
        ParseResult with report and paragraphs
    """
    parser = PolicyPDFParser()
    
    report = PolicyReport(
        source=ReportSource(source),
        report_type=ReportType.MONETARY_POLICY,
        title=title,
        parsed_markdown=text,
        language="zh" if source == "pboc" else "en"
    )
    
    paragraphs = parser._split_paragraphs(text, source)
    
    return ParseResult(
        success=True,
        report=report,
        paragraphs=paragraphs
    )


# Sample data for testing
SAMPLE_PBOC_TEXT = """
# 2024年第三季度中国货币政策执行报告

## 第一部分 货币信贷概况

2024年前三季度，人民银行坚持稳中求进工作总基调，实施稳健的货币政策，加大逆周期调节力度，
推动经济持续回升向好。货币信贷合理增长，社会融资规模平稳扩张，信贷结构持续优化。

当前通胀水平保持温和，CPI同比上涨0.4%，核心CPI同比上涨0.3%。物价水平总体稳定，
为货币政策提供了较大的操作空间。

## 第二部分 货币政策操作

9月份，人民银行下调存款准备金率0.5个百分点，释放长期流动性约1万亿元。同时，
降低政策利率0.2个百分点，引导贷款市场报价利率（LPR）下行，进一步降低实体经济融资成本。

## 第三部分 金融市场运行

前三季度，债券市场发行总量同比增长，收益率曲线整体下移。股票市场波动加大，
人民币汇率在合理均衡水平上保持基本稳定。
"""

SAMPLE_FED_TEXT = """
# Beige Book - December 2024

## National Summary

Economic activity expanded slightly in most Districts since the prior report. Consumer spending 
was mixed, with some Districts reporting modest gains while others noted flat or declining sales.
Employment grew modestly overall, though labor market conditions remained tight.

Prices continued to rise modestly across most Districts, with inflation pressures easing somewhat 
from earlier in the year. Input costs remained elevated but increases have slowed.

## First District - Boston

Economic activity in the First District expanded at a modest pace. Retail contacts reported 
mixed results, with discount retailers outperforming other segments. Manufacturing activity 
was stable, though some firms noted softening demand from abroad.

Employment grew slightly, with continued difficulty filling skilled positions. Wages increased 
moderately, though less rapidly than earlier in the year.
"""


if __name__ == "__main__":
    import sys
    
    print("Testing PDF Parser Module")
    print("=" * 60)
    
    # Test with sample text (no PDF required)
    print("\n1. Testing PBOC text parsing:")
    result = parse_text_report(SAMPLE_PBOC_TEXT, source="pboc", title="2024Q3 PBOC Report")
    print(f"   Success: {result.success}")
    print(f"   Paragraphs found: {len(result.paragraphs)}")
    for p in result.paragraphs[:3]:
        print(f"   - [{p.topic or 'unknown'}] {p.paragraph_text[:50]}...")
    
    print("\n2. Testing Fed text parsing:")
    result = parse_text_report(SAMPLE_FED_TEXT, source="fed", title="December 2024 Beige Book")
    print(f"   Success: {result.success}")
    print(f"   Paragraphs found: {len(result.paragraphs)}")
    for p in result.paragraphs[:3]:
        print(f"   - [{p.topic or 'unknown'}] {p.paragraph_text[:50]}...")
    
    # Test PDF parsing if file provided
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        source = sys.argv[2] if len(sys.argv) > 2 else "pboc"
        
        print(f"\n3. Testing PDF parsing: {pdf_path}")
        parser = PolicyPDFParser(output_dir="./parsed_output")
        result = parser.parse(pdf_path, source=source)
        
        if result.success:
            print(f"   Title: {result.report.title}")
            print(f"   Date: {result.report.report_date}")
            print(f"   Paragraphs: {len(result.paragraphs)}")
        else:
            print(f"   Error: {result.error}")
    
    print("\n" + "=" * 60)
    print("To test with a real PDF:")
    print("  python pdf_parser.py path/to/report.pdf pboc")
    print("  python pdf_parser.py path/to/report.pdf fed")
