"""
Shared Utilities for EconMind-Matrix

This module contains common utility functions used across all layers.
Centralizing these functions eliminates code duplication and ensures
consistent behavior throughout the application.

Created as part of Technical Debt Issue #4 fix.
"""

import re
from typing import Optional


def clean_text(text: Optional[str]) -> Optional[str]:
    """
    Clean text for export by removing newlines and normalizing whitespace.
    
    This function is used across all layers for consistent text cleaning
    when exporting data to various formats (JSON, JSONL, CSV, TSV, etc.).
    
    Args:
        text: The input text to clean, or None
        
    Returns:
        Cleaned text with normalized whitespace, or None/empty if input was None/empty
        
    Examples:
        >>> clean_text("Hello\\nWorld")
        'Hello World'
        >>> clean_text("Multiple   spaces")
        'Multiple spaces'
        >>> clean_text(None)
        None
    """
    if not text:
        return text
    # Replace various newline formats with single space
    text = re.sub(r'[\r\n]+', ' ', text)
    # Remove excessive spaces
    text = re.sub(r' +', ' ', text)
    return text.strip()


# Alias for backward compatibility
clean_export_text = clean_text
