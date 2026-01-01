"""Quick test for Layer 4 components."""
import sys
import asyncio
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

async def test():
    print("=" * 50)
    print("Layer 4 Component Test")
    print("=" * 50)
    
    # Test imports
    print("\n1. Testing imports...")
    from backend import AlignmentEngine, KnowledgeCell, DataLoader
    from backend.aligners import LLMAligner, VectorAligner, RuleAligner, HybridAligner
    print("   ✓ All imports successful")
    
    # Test data loader
    print("\n2. Testing DataLoader...")
    loader = DataLoader()
    stats = await loader.get_statistics()
    print(f"   Layer 1: {stats['layer1']['completed_terms']} terms")
    print(f"   Layer 2: {stats['layer2']['total_paragraphs']} paragraphs")
    print(f"   Layer 3: {stats['layer3']['total_articles']} articles")
    
    # Test Knowledge Cell creation
    print("\n3. Testing KnowledgeCell...")
    from backend.knowledge_cell import create_empty_cell
    cell = create_empty_cell(1, "Inflation")
    print(f"   Created cell: {cell.primary_term}")
    print(f"   Concept ID: {cell.concept_id}")
    
    # Test JSONL serialization
    print("\n4. Testing serialization...")
    jsonl_line = cell.to_jsonl_line()
    restored = KnowledgeCell.from_jsonl_line(jsonl_line)
    assert restored.primary_term == "Inflation"
    print("   ✓ JSONL serialization works")
    
    print("\n" + "=" * 50)
    print("All tests passed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test())
