"""
Layer 4 Alignment API

Provides endpoints to view generated Knowledge Cells and alignment status.
Note: Layer 4 is primarily an offline pipeline. This API serves pre-generated data.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Path to dataset directory
DATASET_DIR = Path(__file__).parent.parent / "dataset"


class AlignmentStats(BaseModel):
    """Summary statistics for alignment data."""
    total_cells: int = 0
    avg_score: float = 0.0
    policy_coverage_pct: float = 0.0
    sentiment_coverage_pct: float = 0.0
    last_updated: Optional[str] = None


class CellsResponse(BaseModel):
    """Response containing Knowledge Cells."""
    cells: List[dict] = []
    stats: AlignmentStats = AlignmentStats()


def find_latest_jsonl() -> Optional[Path]:
    """Find the most recent aligned corpus JSONL file."""
    if not DATASET_DIR.exists():
        return None
    
    jsonl_files = list(DATASET_DIR.glob("aligned_corpus_*.jsonl"))
    if not jsonl_files:
        return None
    
    # Return the most recent by filename (date in name)
    return max(jsonl_files, key=lambda p: p.name)


def load_cells_from_jsonl(filepath: Path) -> List[dict]:
    """Load Knowledge Cells from JSONL file."""
    cells = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    cells.append(json.loads(line))
    except Exception as e:
        print(f"[WARN] Error loading JSONL: {e}")
    return cells


def calculate_stats(cells: List[dict]) -> AlignmentStats:
    """Calculate statistics from cells."""
    if not cells:
        return AlignmentStats()
    
    total = len(cells)
    with_policy = sum(1 for c in cells if c.get('policy_evidence'))
    with_sentiment = sum(1 for c in cells if c.get('sentiment_evidence'))
    
    scores = []
    for c in cells:
        if 'metadata' in c and 'quality_metrics' in c['metadata']:
            scores.append(c['metadata']['quality_metrics'].get('overall_score', 0))
    
    avg_score = sum(scores) / len(scores) if scores else 0.0
    
    return AlignmentStats(
        total_cells=total,
        avg_score=round(avg_score, 3),
        policy_coverage_pct=round((with_policy / total) * 100, 1) if total > 0 else 0,
        sentiment_coverage_pct=round((with_sentiment / total) * 100, 1) if total > 0 else 0,
        last_updated=datetime.now().isoformat()
    )


@router.get("/alignment/cells", response_model=CellsResponse)
async def get_alignment_cells():
    """
    Get all Knowledge Cells from the latest alignment run.
    
    Returns the contents of the most recent aligned_corpus_*.jsonl file.
    """
    jsonl_path = find_latest_jsonl()
    
    if not jsonl_path:
        return CellsResponse(cells=[], stats=AlignmentStats())
    
    cells = load_cells_from_jsonl(jsonl_path)
    stats = calculate_stats(cells)
    
    return CellsResponse(cells=cells, stats=stats)


@router.get("/alignment/stats", response_model=AlignmentStats)
async def get_alignment_stats():
    """Get summary statistics for the alignment data."""
    jsonl_path = find_latest_jsonl()
    
    if not jsonl_path:
        return AlignmentStats()
    
    cells = load_cells_from_jsonl(jsonl_path)
    return calculate_stats(cells)


@router.get("/alignment/cell/{concept_id}")
async def get_cell_by_id(concept_id: str):
    """Get a single Knowledge Cell by concept ID."""
    jsonl_path = find_latest_jsonl()
    
    if not jsonl_path:
        raise HTTPException(status_code=404, detail="No alignment data found")
    
    cells = load_cells_from_jsonl(jsonl_path)
    
    for cell in cells:
        if cell.get('concept_id') == concept_id:
            return cell
    
    raise HTTPException(status_code=404, detail=f"Cell not found: {concept_id}")


@router.get("/alignment/health")
async def alignment_health():
    """Check if alignment data is available."""
    jsonl_path = find_latest_jsonl()
    
    return {
        "status": "ok" if jsonl_path else "no_data",
        "data_file": jsonl_path.name if jsonl_path else None,
        "dataset_dir": str(DATASET_DIR)
    }


# ==================== EXPORT ENDPOINTS ====================

from fastapi.responses import StreamingResponse
import io
import csv

@router.get("/alignment/export/jsonl")
async def export_jsonl():
    """
    Export all Knowledge Cells as JSONL file download.
    """
    jsonl_path = find_latest_jsonl()
    
    if not jsonl_path:
        raise HTTPException(status_code=404, detail="No alignment data found")
    
    # Read the file content
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create streaming response
    filename = f"aligned_corpus_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="application/jsonl",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/alignment/export/csv")
async def export_csv():
    """
    Export Knowledge Cells as flattened CSV file download.
    """
    jsonl_path = find_latest_jsonl()
    
    if not jsonl_path:
        raise HTTPException(status_code=404, detail="No alignment data found")
    
    cells = load_cells_from_jsonl(jsonl_path)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        'concept_id', 'primary_term', 
        'en_term', 'en_summary',
        'zh_term', 'zh_summary',
        'language_count', 'policy_count', 'sentiment_count',
        'quality_score', 'created_at'
    ])
    
    # Data rows
    for cell in cells:
        definitions = cell.get('definitions', {})
        en_def = definitions.get('en', {})
        zh_def = definitions.get('zh', {})
        metadata = cell.get('metadata', {})
        quality = metadata.get('quality_metrics', {})
        
        writer.writerow([
            cell.get('concept_id', ''),
            cell.get('primary_term', ''),
            en_def.get('term', ''),
            en_def.get('summary', '')[:500],  # Truncate for CSV
            zh_def.get('term', ''),
            zh_def.get('summary', '')[:500],
            len(definitions),
            len(cell.get('policy_evidence', [])),
            len(cell.get('sentiment_evidence', [])),
            quality.get('overall_score', 0),
            metadata.get('created_at', '')
        ])
    
    # Return CSV
    output.seek(0)
    filename = f"knowledge_cells_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),  # BOM for Excel
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/alignment/languages")
async def get_available_languages():
    """
    Get list of all languages available in the Knowledge Cells.
    """
    jsonl_path = find_latest_jsonl()
    
    if not jsonl_path:
        return {"languages": [], "language_stats": {}}
    
    cells = load_cells_from_jsonl(jsonl_path)
    
    # Collect all languages and their counts
    lang_stats = {}
    for cell in cells:
        for lang in cell.get('definitions', {}).keys():
            lang_stats[lang] = lang_stats.get(lang, 0) + 1
    
    return {
        "languages": list(lang_stats.keys()),
        "language_stats": lang_stats,
        "total_cells": len(cells)
    }


# ==================== LLM TRAINING FORMAT CONVERTERS ====================

SUPPORTED_LLM_FORMATS = ["alpaca", "sharegpt", "openai", "dolly", "text", "jsonl"]

# Localized template strings for each language
TEMPLATES = {
    "en": {
        "what_is": "What is {term}?",
        "explain": "Explain the economic concept: {term}",
        "policy_question": "How is {term} discussed in policy documents?",
        "sentiment_question": "What is the market sentiment about {term} based on this news?",
        "policy_answer": "This policy text discusses {term} in the context of {source} policy.",
        "sentiment_answer": "The sentiment is {label} with {confidence} confidence.",
        "system_prompt": "You are an expert economist who explains financial concepts clearly.",
        "define": "Define '{term}'"
    },
    "zh": {
        "what_is": "什么是{term}？",
        "explain": "解释经济概念：{term}",
        "policy_question": "{term}在政策文件中是如何讨论的？",
        "sentiment_question": "根据这则新闻，市场对{term}的情绪如何？",
        "policy_answer": "这段政策文本讨论了{term}在{source}政策背景下的内容。",
        "sentiment_answer": "情绪为{label}，置信度{confidence}。",
        "system_prompt": "你是一位专业的经济学家，能够清晰地解释金融概念。",
        "define": "定义'{term}'"
    },
    "ja": {
        "what_is": "{term}とは何ですか？",
        "explain": "経済概念を説明してください：{term}",
        "policy_question": "{term}は政策文書でどのように議論されていますか？",
        "sentiment_question": "このニュースに基づいて、{term}に対する市場のセンチメントは何ですか？",
        "policy_answer": "この政策テキストは、{source}政策の文脈で{term}について議論しています。",
        "sentiment_answer": "センチメントは{label}で、信頼度は{confidence}です。",
        "system_prompt": "あなたは金融の概念を明確に説明する専門のエコノミストです。",
        "define": "'{term}'を定義してください"
    },
    "ko": {
        "what_is": "{term}이란 무엇인가요?",
        "explain": "경제 개념을 설명하세요: {term}",
        "policy_question": "{term}은 정책 문서에서 어떻게 논의되고 있나요?",
        "sentiment_question": "이 뉴스를 바탕으로 {term}에 대한 시장 심리는 어떤가요?",
        "policy_answer": "이 정책 텍스트는 {source} 정책 맥락에서 {term}를 논의합니다.",
        "sentiment_answer": "심리는 {label}이며 신뢰도는 {confidence}입니다.",
        "system_prompt": "당신은 금융 개념을 명확하게 설명하는 전문 경제학자입니다.",
        "define": "'{term}'을 정의하세요"
    },
    "de": {
        "what_is": "Was ist {term}?",
        "explain": "Erklären Sie das wirtschaftliche Konzept: {term}",
        "policy_question": "Wie wird {term} in politischen Dokumenten diskutiert?",
        "sentiment_question": "Was ist die Marktstimmung zu {term} basierend auf dieser Nachricht?",
        "policy_answer": "Dieser Politiktext diskutiert {term} im Kontext der {source}-Politik.",
        "sentiment_answer": "Die Stimmung ist {label} mit {confidence} Vertrauen.",
        "system_prompt": "Sie sind ein Wirtschaftsexperte, der Finanzkonzepte klar erklärt.",
        "define": "Definieren Sie '{term}'"
    },
    "fr": {
        "what_is": "Qu'est-ce que {term} ?",
        "explain": "Expliquez le concept économique : {term}",
        "policy_question": "Comment {term} est-il discuté dans les documents politiques ?",
        "sentiment_question": "Quel est le sentiment du marché concernant {term} selon cette actualité ?",
        "policy_answer": "Ce texte politique discute de {term} dans le contexte de la politique {source}.",
        "sentiment_answer": "Le sentiment est {label} avec une confiance de {confidence}.",
        "system_prompt": "Vous êtes un économiste expert qui explique clairement les concepts financiers.",
        "define": "Définissez '{term}'"
    },
    "es": {
        "what_is": "¿Qué es {term}?",
        "explain": "Explique el concepto económico: {term}",
        "policy_question": "¿Cómo se discute {term} en los documentos de política?",
        "sentiment_question": "¿Cuál es el sentimiento del mercado sobre {term} según esta noticia?",
        "policy_answer": "Este texto de política discute {term} en el contexto de la política {source}.",
        "sentiment_answer": "El sentimiento es {label} con {confidence} de confianza.",
        "system_prompt": "Eres un economista experto que explica conceptos financieros con claridad.",
        "define": "Defina '{term}'"
    },
    "ru": {
        "what_is": "Что такое {term}?",
        "explain": "Объясните экономическое понятие: {term}",
        "policy_question": "Как {term} обсуждается в политических документах?",
        "sentiment_question": "Каково рыночное настроение относительно {term} на основе этой новости?",
        "policy_answer": "Этот политический текст обсуждает {term} в контексте политики {source}.",
        "sentiment_answer": "Настроение {label} с уверенностью {confidence}.",
        "system_prompt": "Вы эксперт-экономист, который ясно объясняет финансовые концепции.",
        "define": "Дайте определение '{term}'"
    }
}


def get_template(lang: str, key: str) -> str:
    """Get localized template string, fallback to English."""
    if lang in TEMPLATES and key in TEMPLATES[lang]:
        return TEMPLATES[lang][key]
    return TEMPLATES["en"].get(key, "")


def cell_to_alpaca(cell: dict, lang: str = "en") -> List[dict]:
    """
    Convert Knowledge Cell to Alpaca format.
    Format: {"instruction": str, "input": str, "output": str}
    Uses localized template strings based on language.
    """
    results = []
    definitions = cell.get('definitions', {})
    primary_term = cell.get('primary_term', '')
    
    # Definition instruction
    if lang in definitions:
        defn = definitions[lang]
        term = defn.get('term', primary_term)
        results.append({
            "instruction": get_template(lang, "explain").format(term=term),
            "input": "",
            "output": defn.get('summary', '')
        })
    
    # Policy evidence - only include if language matches source
    lang_source_map = {'zh': 'pboc', 'en': 'fed'}
    expected_source = lang_source_map.get(lang, 'fed')
    
    for evidence in cell.get('policy_evidence', []):
        if evidence.get('source', '').lower() != expected_source:
            continue  # Skip non-matching language evidence
        term = definitions.get(lang, {}).get('term', primary_term)
        source = evidence.get('source', 'central bank').upper()
        results.append({
            "instruction": get_template(lang, "policy_question").format(term=term),
            "input": evidence.get('text', '')[:500],
            "output": get_template(lang, "policy_answer").format(term=term, source=source)
        })
    
    # Sentiment evidence - include all (news titles can be any language)
    for evidence in cell.get('sentiment_evidence', []):
        sentiment = evidence.get('sentiment', {})
        term = definitions.get(lang, {}).get('term', primary_term)
        label = sentiment.get('label', 'neutral')
        confidence = f"{sentiment.get('confidence', 0):.0%}"
        results.append({
            "instruction": get_template(lang, "sentiment_question").format(term=term),
            "input": evidence.get('title', ''),
            "output": get_template(lang, "sentiment_answer").format(label=label, confidence=confidence)
        })
    
    return results


def cell_to_sharegpt(cell: dict, lang: str = "en") -> dict:
    """
    Convert Knowledge Cell to ShareGPT conversation format.
    Format: {"conversations": [{"from": "human"|"gpt", "value": str}]}
    Uses localized template strings for pure monolingual output.
    """
    conversations = []
    definitions = cell.get('definitions', {})
    primary_term = cell.get('primary_term', '')
    
    # Use the selected language only
    if lang in definitions:
        defn = definitions[lang]
        term = defn.get('term', primary_term)
        conversations.append({"from": "human", "value": get_template(lang, "what_is").format(term=term)})
        conversations.append({"from": "gpt", "value": defn.get('summary', '')})
    elif definitions:
        # Fallback to first available language
        first_lang = list(definitions.keys())[0]
        defn = definitions[first_lang]
        term = defn.get('term', primary_term)
        conversations.append({"from": "human", "value": get_template(lang, "what_is").format(term=term)})
        conversations.append({"from": "gpt", "value": defn.get('summary', '')})
    
    # Policy context - only include if language matches source
    # 'pboc' for Chinese, 'fed' for English
    lang_source_map = {'zh': 'pboc', 'en': 'fed'}
    expected_source = lang_source_map.get(lang, 'fed')
    
    matching_evidence = [e for e in cell.get('policy_evidence', []) 
                         if e.get('source', '').lower() == expected_source]
    
    if matching_evidence:
        evidence = matching_evidence[0]
        term = definitions.get(lang, {}).get('term', primary_term)
        conversations.append({"from": "human", "value": get_template(lang, "policy_question").format(term=term)})
        conversations.append({"from": "gpt", "value": evidence.get('text', '')[:500]})
    
    return {"conversations": conversations}


def cell_to_openai(cell: dict, lang: str = "en") -> dict:
    """
    Convert Knowledge Cell to OpenAI messages format.
    Format: {"messages": [{"role": "system"|"user"|"assistant", "content": str}]}
    Uses localized template strings.
    """
    messages = [
        {"role": "system", "content": get_template(lang, "system_prompt")}
    ]
    
    definitions = cell.get('definitions', {})
    primary_term = cell.get('primary_term', '')
    
    if lang in definitions:
        defn = definitions[lang]
        term = defn.get('term', primary_term)
        messages.append({"role": "user", "content": get_template(lang, "define").format(term=term)})
        messages.append({"role": "assistant", "content": defn.get('summary', '')})
    
    # Add policy context - only include if language matches source
    lang_source_map = {'zh': 'pboc', 'en': 'fed'}
    expected_source = lang_source_map.get(lang, 'fed')
    
    matching_evidence = [e for e in cell.get('policy_evidence', [])
                         if e.get('source', '').lower() == expected_source]
    
    if matching_evidence:
        evidence = matching_evidence[0]
        term = definitions.get(lang, {}).get('term', primary_term)
        messages.append({"role": "user", "content": get_template(lang, "policy_question").format(term=term)})
        messages.append({"role": "assistant", "content": evidence.get('text', '')[:500]})
    
    return {"messages": messages}


def cell_to_dolly(cell: dict, lang: str = "en") -> List[dict]:
    """
    Convert Knowledge Cell to Dolly format with context.
    Format: {"instruction": str, "context": str, "response": str}
    Uses localized template strings.
    """
    results = []
    definitions = cell.get('definitions', {})
    primary_term = cell.get('primary_term', '')
    
    if lang in definitions:
        defn = definitions[lang]
        term = defn.get('term', primary_term)
        
        # Basic definition
        results.append({
            "instruction": get_template(lang, "explain").format(term=term),
            "context": "",
            "response": defn.get('summary', '')
        })
        
        # With policy context - only include if language matches source
        lang_source_map = {'zh': 'pboc', 'en': 'fed'}
        expected_source = lang_source_map.get(lang, 'fed')
        
        for evidence in cell.get('policy_evidence', []):
            if evidence.get('source', '').lower() != expected_source:
                continue  # Skip non-matching language evidence
            source = evidence.get('source', 'central bank').upper()
            results.append({
                "instruction": get_template(lang, "policy_question").format(term=term),
                "context": evidence.get('text', '')[:500],
                "response": get_template(lang, "policy_answer").format(term=term, source=source)
            })
    
    return results


def cell_to_text(cell: dict, lang: str = "en") -> str:
    """
    Convert Knowledge Cell to plain text Q&A format.
    Uses localized template strings for pure monolingual output.
    """
    lines = []
    definitions = cell.get('definitions', {})
    primary_term = cell.get('primary_term', '')
    
    if lang in definitions:
        defn = definitions[lang]
        term = defn.get('term', primary_term)
        # Use Q: A: format with localized question
        question = get_template(lang, "what_is").format(term=term)
        lines.append(f"Q: {question}")
        lines.append(f"A: {defn.get('summary', '')}")
        lines.append("")
    elif definitions:
        # Fallback to first available language
        first_lang = list(definitions.keys())[0]
        defn = definitions[first_lang]
        term = defn.get('term', primary_term)
        question = get_template(lang, "what_is").format(term=term)
        lines.append(f"Q: {question}")
        lines.append(f"A: {defn.get('summary', '')}")
        lines.append("")
    
    return "\n".join(lines)


def convert_cell_to_format(cell: dict, format_type: str, lang: str = "en") -> any:
    """Convert a cell to the specified format."""
    if format_type == "alpaca":
        return cell_to_alpaca(cell, lang)
    elif format_type == "sharegpt":
        return cell_to_sharegpt(cell, lang)
    elif format_type == "openai":
        return cell_to_openai(cell, lang)
    elif format_type == "dolly":
        return cell_to_dolly(cell, lang)
    elif format_type == "text":
        return cell_to_text(cell, lang)
    elif format_type == "jsonl":
        return cell
    else:
        raise ValueError(f"Unsupported format: {format_type}")


# ==================== PER-CELL EXPORT ENDPOINTS ====================

@router.get("/alignment/cell/{concept_id}/export")
async def export_single_cell(concept_id: str, format: str = "jsonl", lang: str = "en"):
    """
    Export a single Knowledge Cell in the specified LLM training format.
    
    Args:
        concept_id: The concept ID (e.g., TERM_1)
        format: Export format (alpaca, sharegpt, openai, dolly, text, jsonl)
        lang: Primary language for generation (en, zh)
    """
    if format not in SUPPORTED_LLM_FORMATS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported format. Supported: {SUPPORTED_LLM_FORMATS}"
        )
    
    jsonl_path = find_latest_jsonl()
    if not jsonl_path:
        raise HTTPException(status_code=404, detail="No alignment data found")
    
    cells = load_cells_from_jsonl(jsonl_path)
    
    # Find the cell
    cell = next((c for c in cells if c.get('concept_id') == concept_id), None)
    if not cell:
        raise HTTPException(status_code=404, detail=f"Cell not found: {concept_id}")
    
    # Convert to format
    result = convert_cell_to_format(cell, format, lang)
    
    # For text format, return as plain text
    if format == "text":
        return StreamingResponse(
            io.BytesIO(result.encode('utf-8')),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={concept_id}_{format}.txt"}
        )
    
    # For other formats, return as JSON download
    content = json.dumps(result, ensure_ascii=False, indent=2)
    filename = f"{concept_id}_{format}.json"
    
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==================== LOCAL TRANSLATION (ARGOSTRANSLATE) ====================

class LocalTranslateRequest(BaseModel):
    """Request body for local translation export."""
    format: str = "sharegpt"
    lang: str = "zh"


def translate_with_argos(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate text using argostranslate (offline neural MT).
    
    Requires: pip install argostranslate
    Models: Download from https://www.argosopentech.com/argospm/index/
    
    Returns original text if translation fails.
    """
    try:
        import argostranslate.translate
        
        # Try to translate
        translated = argostranslate.translate.translate(text, source_lang, target_lang)
        return translated if translated else text
    
    except ImportError:
        print("[WARN] argostranslate not installed. Install with: pip install argostranslate")
        return text
    except Exception as e:
        print(f"[WARN] Argos translation failed: {e}")
        return text


@router.post("/alignment/cell/{concept_id}/export/local-translate")
async def export_cell_local_translate(concept_id: str, request: LocalTranslateRequest):
    """
    Export a single Knowledge Cell with local translation using argostranslate.
    
    This is a FREE translation option that doesn't require API keys.
    Requires argostranslate library and language models to be installed.
    
    Install: pip install argostranslate
    Then download models for your language pair.
    """
    jsonl_path = find_latest_jsonl()
    if not jsonl_path:
        raise HTTPException(status_code=404, detail="No alignment data found")
    
    cells = load_cells_from_jsonl(jsonl_path)
    cell = next((c for c in cells if c.get('concept_id') == concept_id), None)
    if not cell:
        raise HTTPException(status_code=404, detail=f"Cell not found: {concept_id}")
    
    policy_evidence = cell.get('policy_evidence', [])
    definitions = cell.get('definitions', {})
    primary_term = cell.get('primary_term', '')
    
    results = []
    
    for evidence in policy_evidence:
        source = evidence.get('source', '').lower()
        text = evidence.get('text', '')[:500]
        
        # Determine if translation is needed
        needs_translation = (request.lang == 'zh' and source == 'fed') or \
                           (request.lang == 'en' and source == 'pboc')
        
        if needs_translation:
            source_lang = 'en' if source == 'fed' else 'zh'
            translated_text = translate_with_argos(text, source_lang, request.lang)
            
            # If translation failed (returned same text), add a note
            if translated_text == text:
                translated_text = f"[Translation unavailable] {text}"
            
            term = definitions.get(request.lang, {}).get('term', primary_term)
            conversation = {
                "conversations": [
                    {"from": "human", "value": get_template(request.lang, "policy_question").format(term=term)},
                    {"from": "gpt", "value": translated_text}
                ]
            }
            results.append(conversation)
    
    # Include native content (no metadata)
    native_result = convert_cell_to_format(cell, request.format, request.lang)
    if isinstance(native_result, list):
        for item in native_result:
            # Remove any metadata if present
            if isinstance(item, dict) and 'metadata' in item:
                del item['metadata']
            results.append(item)
    else:
        if isinstance(native_result, dict) and 'metadata' in native_result:
            del native_result['metadata']
        results.append(native_result)
    
    content = json.dumps(results, ensure_ascii=False, indent=2)
    filename = f"{concept_id}_{request.format}_{request.lang}_local.jsonl"
    
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


class CrossLingualExportRequest(BaseModel):
    """Request body for cross-lingual cell export."""
    format: str = "sharegpt"
    lang: str = "zh"
    provider: str = "openai"
    api_key: str = ""
    model: str = ""


@router.post("/alignment/cell/{concept_id}/export/cross-lingual")
async def export_cell_cross_lingual(concept_id: str, request: CrossLingualExportRequest):
    """
    Export a single Knowledge Cell with cross-lingual LLM translation.
    
    This endpoint generates bilingual training data by:
    1. Including native language content
    2. Using LLM API to translate/analyze content in the target language
    
    Args:
        concept_id: The concept ID (e.g., TERM_1)
        request.format: Export format (alpaca, sharegpt, etc.)
        request.lang: Target language for translation
        request.provider: LLM API provider (openai/gemini)
        request.api_key: API key for LLM service
        request.model: Model name (optional)
    """
    import httpx
    
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required for cross-lingual export")
    
    jsonl_path = find_latest_jsonl()
    if not jsonl_path:
        raise HTTPException(status_code=404, detail="No alignment data found")
    
    cells = load_cells_from_jsonl(jsonl_path)
    cell = next((c for c in cells if c.get('concept_id') == concept_id), None)
    if not cell:
        raise HTTPException(status_code=404, detail=f"Cell not found: {concept_id}")
    
    # Get policy evidence that needs translation
    policy_evidence = cell.get('policy_evidence', [])
    definitions = cell.get('definitions', {})
    primary_term = cell.get('primary_term', '')
    
    # Determine translation direction
    # If lang=zh and source=fed, translate FED->ZH
    # If lang=en and source=pboc, translate PBOC->EN
    results = []
    
    for evidence in policy_evidence:
        source = evidence.get('source', '').lower()
        text = evidence.get('text', '')[:500]
        
        # Check if cross-lingual translation is needed
        needs_translation = (request.lang == 'zh' and source == 'fed') or \
                           (request.lang == 'en' and source == 'pboc')
        
        if needs_translation:
            # Call LLM API for translation
            translated_text = await call_llm_translation(
                text=text,
                source_lang='en' if source == 'fed' else 'zh',
                target_lang=request.lang,
                term=definitions.get(request.lang, {}).get('term', primary_term),
                provider=request.provider,
                api_key=request.api_key,
                model=request.model
            )
            
            if translated_text:
                term = definitions.get(request.lang, {}).get('term', primary_term)
                conversation = {
                    "conversations": [
                        {"from": "human", "value": get_template(request.lang, "policy_question").format(term=term)},
                        {"from": "gpt", "value": translated_text}
                    ]
                }
                results.append(conversation)
    
    # Include native content (no metadata)
    native_result = convert_cell_to_format(cell, request.format, request.lang)
    if isinstance(native_result, list):
        for item in native_result:
            if isinstance(item, dict) and 'metadata' in item:
                del item['metadata']
            results.append(item)
    else:
        if isinstance(native_result, dict) and 'metadata' in native_result:
            del native_result['metadata']
        results.append(native_result)
    
    content = json.dumps(results, ensure_ascii=False, indent=2)
    filename = f"{concept_id}_{request.format}_{request.lang}_crosslingual.jsonl"
    
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


async def call_llm_translation(
    text: str,
    source_lang: str,
    target_lang: str,
    term: str,
    provider: str,
    api_key: str,
    model: str = ""
) -> str:
    """Call LLM API to translate financial text."""
    import httpx
    
    # Build prompt based on direction
    if target_lang == 'zh':
        system = "你是一位资深中国宏观经济学家。请用专业的中文金融术语翻译并分析以下美联储政策文本。"
        user = f"请将以下美联储政策声明翻译成专业中文，并结合'{term}'的概念进行简要分析：\n\n{text}"
    else:
        system = "You are a senior Wall Street analyst. Translate and analyze this PBOC policy text in professional English."
        user = f"Translate this PBOC policy statement into professional English, with analysis relevant to '{term}':\n\n{text}"
    
    try:
        if provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model or "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                "temperature": 0.7,
                "max_tokens": 800
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=60)
                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content']
        
        elif provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model or 'gemini-1.5-flash'}:generateContent"
            params = {"key": api_key}
            payload = {
                "contents": [{"role": "user", "parts": [{"text": f"{system}\n\n{user}"}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, params=params, timeout=60)
                if response.status_code == 200:
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
    
    except Exception as e:
        print(f"[WARN] LLM translation failed: {e}")
    
    return ""


@router.get("/alignment/export/llm/{format_type}")
async def export_all_llm_format(format_type: str, lang: str = "en"):
    """
    Export all Knowledge Cells in the specified LLM training format.
    
    Args:
        format_type: Export format (alpaca, sharegpt, openai, dolly, text)
        lang: Primary language for generation (en, zh)
    """
    if format_type not in SUPPORTED_LLM_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Supported: {SUPPORTED_LLM_FORMATS}"
        )
    
    jsonl_path = find_latest_jsonl()
    if not jsonl_path:
        raise HTTPException(status_code=404, detail="No alignment data found")
    
    cells = load_cells_from_jsonl(jsonl_path)
    
    # Convert all cells
    all_results = []
    for cell in cells:
        result = convert_cell_to_format(cell, format_type, lang)
        if isinstance(result, list):
            all_results.extend(result)
        else:
            all_results.append(result)
    
    # Generate appropriate output
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if format_type == "text":
        content = "\n\n---\n\n".join(all_results) if isinstance(all_results[0], str) else ""
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=training_data_{format_type}_{timestamp}.txt"}
        )
    
    # JSONL output for LLM training
    lines = [json.dumps(item, ensure_ascii=False) for item in all_results]
    content = "\n".join(lines)
    
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="application/jsonl",
        headers={"Content-Disposition": f"attachment; filename=training_data_{format_type}_{timestamp}.jsonl"}
    )


@router.get("/alignment/formats")
async def get_supported_formats():
    """Get list of supported LLM training formats with descriptions."""
    return {
        "formats": [
            {"name": "alpaca", "description": "Alpaca instruction format", "structure": "{instruction, input, output}"},
            {"name": "sharegpt", "description": "ShareGPT conversation format", "structure": "{conversations: [{from, value}]}"},
            {"name": "openai", "description": "OpenAI messages format", "structure": "{messages: [{role, content}]}"},
            {"name": "dolly", "description": "Dolly context-aware format", "structure": "{instruction, context, response}"},
            {"name": "text", "description": "Plain text Q&A pairs", "structure": "Q: ... A: ..."},
            {"name": "jsonl", "description": "Raw Knowledge Cell JSON", "structure": "Complete cell data"}
        ]
    }


# ==================== CROSS-LINGUAL AUGMENTATION ====================

class AugmentationRequest(BaseModel):
    """Request body for triggering cross-lingual augmentation."""
    provider: str = "openai"  # openai or gemini
    api_key: str = ""
    api_base: str = ""
    model: str = ""
    ratio: float = 0.3
    batch_size: int = 5


class AugmentationStatus(BaseModel):
    """Status of augmentation operation."""
    is_running: bool = False
    progress: float = 0.0
    message: str = ""
    output_file: str = ""
    fed_count: int = 0
    pboc_count: int = 0


# Global status tracker for augmentation
_augmentation_status = AugmentationStatus()


@router.get("/alignment/augmentation/status")
async def get_augmentation_status():
    """Get current augmentation status."""
    # Check for existing augmented output files
    aug_files = list(DATASET_DIR.glob("cross_lingual_*.jsonl")) if DATASET_DIR.exists() else []
    latest_file = max(aug_files, key=lambda p: p.stat().st_mtime).name if aug_files else ""
    
    # Get policy evidence counts
    jsonl_file = find_latest_jsonl()
    fed_count = 0
    pboc_count = 0
    
    if jsonl_file:
        cells = load_cells_from_jsonl(jsonl_file)
        for cell in cells:
            for evidence in cell.get('policy_evidence', []):
                source = evidence.get('source', '').lower()
                if source == 'fed':
                    fed_count += 1
                elif source == 'pboc':
                    pboc_count += 1
    
    return {
        "is_running": _augmentation_status.is_running,
        "progress": _augmentation_status.progress,
        "message": _augmentation_status.message,
        "latest_output": latest_file,
        "fed_count": fed_count,
        "pboc_count": pboc_count,
        "support_info": {
            "providers": ["openai", "gemini"],
            "default_models": {
                "openai": "gpt-4o-mini",
                "gemini": "gemini-1.5-flash"
            }
        }
    }


@router.post("/alignment/augmentation/run")
async def run_augmentation(request: AugmentationRequest):
    """
    Trigger cross-lingual augmentation (async background task).
    
    NOTE: This endpoint starts the augmentation script as a background process.
    Check /augmentation/status for progress.
    """
    global _augmentation_status
    
    if _augmentation_status.is_running:
        raise HTTPException(status_code=409, detail="Augmentation already in progress")
    
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    # Find input file
    input_file = find_latest_jsonl()
    if not input_file:
        raise HTTPException(status_code=404, detail="No aligned corpus found. Run alignment pipeline first.")
    
    # Prepare output path
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = DATASET_DIR / f"cross_lingual_{timestamp}.jsonl"
    
    # Start augmentation in background
    import subprocess
    import threading
    
    script_path = Path(__file__).parent.parent / "layer4_alignment" / "scripts" / "cross_lingual_augmentor.py"
    
    cmd = [
        "python", str(script_path),
        "--input", str(input_file),
        "--output", str(output_file),
        "--provider", request.provider,
        "--api-key", request.api_key,
        "--ratio", str(request.ratio),
        "--batch-size", str(request.batch_size)
    ]
    
    if request.api_base:
        cmd.extend(["--api-base", request.api_base])
    if request.model:
        cmd.extend(["--model", request.model])
    
    def run_in_background():
        global _augmentation_status
        _augmentation_status.is_running = True
        _augmentation_status.message = "Starting augmentation..."
        _augmentation_status.progress = 0.0
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                _augmentation_status.message = "Augmentation complete!"
                _augmentation_status.output_file = output_file.name
            else:
                _augmentation_status.message = f"Error: {result.stderr[:200]}"
        except Exception as e:
            _augmentation_status.message = f"Failed: {str(e)}"
        finally:
            _augmentation_status.is_running = False
            _augmentation_status.progress = 1.0
    
    thread = threading.Thread(target=run_in_background)
    thread.start()
    
    return {
        "status": "started",
        "message": "Augmentation started in background. Check /augmentation/status for progress.",
        "output_file": output_file.name
    }


@router.get("/alignment/augmentation/download/{filename}")
async def download_augmented_file(filename: str):
    """Download a generated augmented training file."""
    filepath = DATASET_DIR / filename
    
    if not filepath.exists() or not filename.startswith("cross_lingual_"):
        raise HTTPException(status_code=404, detail="File not found")
    
    content = filepath.read_text(encoding='utf-8')
    
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="application/jsonl",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
