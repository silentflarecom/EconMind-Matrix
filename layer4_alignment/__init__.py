"""
Layer 4: Offline Multi-Dimensional Semantic Alignment Pipeline

This module consumes completed data from Layers 1-3 and produces 
publication-ready aligned datasets (Knowledge Cells).

Usage:
    from layer4_alignment import AlignmentEngine
    
    engine = AlignmentEngine(config_path="config/alignment_config.yaml")
    await engine.run_full_alignment()
"""

from pathlib import Path

# Module version
__version__ = "4.0.0"

# Module root path
MODULE_ROOT = Path(__file__).parent

# Default paths
DEFAULT_CONFIG_PATH = MODULE_ROOT / "config" / "alignment_config.yaml"
DEFAULT_OUTPUT_DIR = MODULE_ROOT.parent / "dataset"
