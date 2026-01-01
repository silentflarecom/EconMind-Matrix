"""
JSONL Exporter

Exports Knowledge Cells to JSON Lines format.
"""

import gzip
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from ..knowledge_cell import KnowledgeCell


class JSONLExporter:
    """
    Exports Knowledge Cells to JSONL format.
    
    Each line is a valid JSON object representing one Knowledge Cell.
    Optionally supports gzip compression.
    """
    
    def __init__(
        self,
        output_dir: str = "dataset",
        filename_template: str = "aligned_corpus_{date}",
        compress: bool = False
    ):
        self.output_dir = Path(output_dir)
        self.filename_template = filename_template
        self.compress = compress
    
    def export(
        self,
        cells: List[KnowledgeCell],
        output_path: Optional[str] = None
    ) -> str:
        """
        Export cells to JSONL file.
        
        Args:
            cells: List of KnowledgeCell objects
            output_path: Optional explicit output path
            
        Returns:
            Path to the created file
        """
        if output_path:
            filepath = Path(output_path)
        else:
            self.output_dir.mkdir(exist_ok=True, parents=True)
            date_str = datetime.now().strftime("%Y%m%d")
            filename = self.filename_template.format(date=date_str)
            filepath = self.output_dir / f"{filename}.jsonl"
        
        filepath.parent.mkdir(exist_ok=True, parents=True)
        
        if self.compress:
            filepath = Path(str(filepath) + ".gz")
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                for cell in cells:
                    f.write(cell.to_jsonl_line() + '\n')
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                for cell in cells:
                    f.write(cell.to_jsonl_line() + '\n')
        
        return str(filepath)
    
    @staticmethod
    def load(filepath: str) -> List[KnowledgeCell]:
        """
        Load Knowledge Cells from JSONL file.
        
        Args:
            filepath: Path to JSONL file (supports .gz)
            
        Returns:
            List of KnowledgeCell objects
        """
        cells = []
        path = Path(filepath)
        
        if path.suffix == '.gz':
            opener = gzip.open(path, 'rt', encoding='utf-8')
        else:
            opener = open(path, 'r', encoding='utf-8')
        
        with opener as f:
            for line in f:
                line = line.strip()
                if line:
                    cells.append(KnowledgeCell.from_jsonl_line(line))
        
        return cells
