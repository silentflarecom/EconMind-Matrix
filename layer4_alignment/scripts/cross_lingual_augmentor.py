"""
Cross-Lingual Augmentation Script for Financial LLM Training Data

This script implements a "Cross-Lingual Augmentation Strategy" (2x2 Matrix) to ensure
the model understands both FED and PBOC policies in both English and Chinese.

Strategy:
- FED (EN) → Native EN (70%) + LLM-Generated ZH Analysis (30%)
- PBOC (ZH) → Native ZH (70%) + LLM-Generated EN Analysis (30%)

Author: EconMind-Matrix
"""

import os
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import random

# Optional imports for async HTTP
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("[WARN] aiohttp not installed. Install with: pip install aiohttp")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("[WARN] pandas not installed. Install with: pip install pandas")


# ==================== CONFIGURATION ====================

@dataclass
class AugmentationConfig:
    """Configuration for cross-lingual augmentation."""
    
    # API Settings
    api_provider: str = "openai"  # "openai" or "gemini"
    api_key: str = ""  # User must provide
    api_base_url: str = ""  # Optional custom endpoint
    model_name: str = ""  # Model to use
    
    # Processing Settings
    augmentation_ratio: float = 0.3  # 30% augmented, 70% native
    batch_size: int = 5  # Concurrent API calls
    max_retries: int = 3
    timeout_seconds: int = 60
    
    # Output Settings
    output_format: str = "sharegpt"  # Currently only sharegpt supported
    include_metadata: bool = True
    
    def __post_init__(self):
        """Set default model names based on provider."""
        if not self.model_name:
            if self.api_provider == "openai":
                self.model_name = "gpt-4o-mini"
            elif self.api_provider == "gemini":
                self.model_name = "gemini-1.5-flash"


# ==================== PROMPTS ====================

# Cross-lingual analysis prompts with economic domain expertise
PROMPTS = {
    "fed_to_zh": {
        "system": "你是一位资深中国宏观经济学家和金融分析师。你精通美联储货币政策分析，能够用专业的中文金融术语解读美联储声明。",
        "user_template": """请以中国宏观经济学家的视角，用专业的中文金融术语分析以下美联储声明：

【美联储原文】
{text}

请提供：
1. 核心政策要点的中文解读
2. 对中国经济的潜在影响分析
3. 使用专业中文金融术语，如"量化宽松"、"联邦基金利率"等"""
    },
    
    "pboc_to_en": {
        "system": "You are a senior Wall Street analyst and macro-economist specializing in Chinese monetary policy. You translate PBOC policy into professional English financial terminology.",
        "user_template": """As a Wall Street analyst, provide a professional English analysis of this PBOC statement:

【PBOC Original (Chinese)】
{text}

Please provide:
1. Key policy points in professional English
2. Implications for global markets
3. Use proper financial terminology like "monetary easing", "reserve requirement ratio", etc."""
    }
}


# ==================== DATA LOADER ====================

class DataLoader:
    """Load and segregate data by source language."""
    
    def __init__(self, input_path: str):
        self.input_path = Path(input_path)
    
    def load_aligned_corpus(self) -> List[Dict]:
        """Load Knowledge Cells from JSONL file."""
        cells = []
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")
        
        with open(self.input_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    cells.append(json.loads(line))
        
        print(f"[INFO] Loaded {len(cells)} Knowledge Cells from {self.input_path}")
        return cells
    
    def extract_policy_evidence(self, cells: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract and segregate policy evidence by source.
        
        Returns:
            fed_en: FED policy evidence (English source)
            pboc_zh: PBOC policy evidence (Chinese source)
        """
        fed_en = []
        pboc_zh = []
        
        for cell in cells:
            term = cell.get('primary_term', '')
            definitions = cell.get('definitions', {})
            
            for evidence in cell.get('policy_evidence', []):
                source = evidence.get('source', '').lower()
                text = evidence.get('text', '')
                
                record = {
                    'source': source,
                    'text': text,
                    'term': term,
                    'term_en': definitions.get('en', {}).get('term', term),
                    'term_zh': definitions.get('zh', {}).get('term', term),
                    'paragraph_id': evidence.get('paragraph_id', ''),
                    'topic': evidence.get('topic', ''),
                    'alignment_score': evidence.get('alignment_scores', {}).get('final', 0)
                }
                
                if source == 'fed':
                    record['language'] = 'en'
                    fed_en.append(record)
                elif source == 'pboc':
                    record['language'] = 'zh'
                    pboc_zh.append(record)
        
        print(f"[INFO] Extracted {len(fed_en)} FED (EN) + {len(pboc_zh)} PBOC (ZH) policy records")
        return fed_en, pboc_zh


# ==================== LLM AUGMENTER ====================

class LLMAugmenter:
    """Asynchronous LLM-based cross-lingual augmentation."""
    
    def __init__(self, config: AugmentationConfig):
        self.config = config
        self._validate_config()
    
    def _validate_config(self):
        """Validate API configuration."""
        if not self.config.api_key:
            raise ValueError("API key is required. Set via config or environment variable.")
        
        if self.config.api_provider not in ["openai", "gemini"]:
            raise ValueError(f"Unsupported API provider: {self.config.api_provider}")
    
    async def _call_openai(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Call OpenAI API asynchronously."""
        if not AIOHTTP_AVAILABLE:
            return self._call_openai_sync(system_prompt, user_prompt)
        
        url = self.config.api_base_url or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.config.max_retries):
                try:
                    async with session.post(
                        url, 
                        json=payload, 
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data['choices'][0]['message']['content']
                        else:
                            error_text = await response.text()
                            print(f"[WARN] OpenAI API error (attempt {attempt+1}): {response.status} - {error_text}")
                except Exception as e:
                    print(f"[WARN] OpenAI API exception (attempt {attempt+1}): {e}")
                
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _call_openai_sync(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Synchronous fallback for OpenAI API."""
        try:
            import openai
            client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base_url or None
            )
            response = client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[WARN] OpenAI sync call failed: {e}")
            return None
    
    async def _call_gemini(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Call Gemini API asynchronously."""
        if not AIOHTTP_AVAILABLE:
            return self._call_gemini_sync(system_prompt, user_prompt)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.model_name}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.config.api_key}
        
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000
            }
        }
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.config.max_retries):
                try:
                    async with session.post(
                        url,
                        json=payload,
                        headers=headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data['candidates'][0]['content']['parts'][0]['text']
                        else:
                            error_text = await response.text()
                            print(f"[WARN] Gemini API error (attempt {attempt+1}): {response.status}")
                except Exception as e:
                    print(f"[WARN] Gemini API exception (attempt {attempt+1}): {e}")
                
                await asyncio.sleep(2 ** attempt)
        
        return None
    
    def _call_gemini_sync(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Synchronous fallback for Gemini API."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.api_key)
            model = genai.GenerativeModel(self.config.model_name)
            response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
            return response.text
        except Exception as e:
            print(f"[WARN] Gemini sync call failed: {e}")
            return None
    
    async def augment_single(self, text: str, direction: str) -> Optional[str]:
        """
        Augment a single text in the specified direction.
        
        Args:
            text: Source text to augment
            direction: "fed_to_zh" or "pboc_to_en"
        
        Returns:
            Augmented text in target language, or None if failed
        """
        if direction not in PROMPTS:
            raise ValueError(f"Unknown direction: {direction}")
        
        prompt_config = PROMPTS[direction]
        system_prompt = prompt_config["system"]
        user_prompt = prompt_config["user_template"].format(text=text)
        
        if self.config.api_provider == "openai":
            return await self._call_openai(system_prompt, user_prompt)
        elif self.config.api_provider == "gemini":
            return await self._call_gemini(system_prompt, user_prompt)
        
        return None
    
    async def augment_batch(self, records: List[Dict], direction: str) -> List[Dict]:
        """
        Augment a batch of records concurrently.
        
        Returns list of augmented records with 'augmented_text' field.
        """
        augmented = []
        
        # Process in batches for rate limiting
        for i in range(0, len(records), self.config.batch_size):
            batch = records[i:i + self.config.batch_size]
            
            tasks = [
                self.augment_single(record['text'], direction)
                for record in batch
            ]
            
            results = await asyncio.gather(*tasks)
            
            for record, result in zip(batch, results):
                if result:
                    aug_record = record.copy()
                    aug_record['augmented_text'] = result
                    aug_record['augmentation_direction'] = direction
                    augmented.append(aug_record)
            
            print(f"[INFO] Processed batch {i//self.config.batch_size + 1}, "
                  f"successful: {len([r for r in results if r])}/{len(batch)}")
            
            # Small delay between batches to avoid rate limits
            await asyncio.sleep(1)
        
        return augmented


# ==================== MIXING STRATEGY ====================

class MixingStrategy:
    """Implement 70/30 native/augmented mixing ratio."""
    
    def __init__(self, augmentation_ratio: float = 0.3):
        self.augmentation_ratio = augmentation_ratio
    
    def mix_data(
        self, 
        native_fed: List[Dict], 
        native_pboc: List[Dict],
        augmented_fed_zh: List[Dict],
        augmented_pboc_en: List[Dict]
    ) -> List[Dict]:
        """
        Mix native and augmented data according to the configured ratio.
        
        Economic Logic:
        - Native data (70%): Ensures model learns authentic policy language
        - Augmented data (30%): Enables cross-lingual understanding
        
        This produces a balanced dataset where the model can understand:
        - FED policies in both English (native) and Chinese (augmented)
        - PBOC policies in both Chinese (native) and English (augmented)
        """
        # Calculate target counts
        total_native = len(native_fed) + len(native_pboc)
        target_augmented = int(total_native * self.augmentation_ratio / (1 - self.augmentation_ratio))
        
        # Limit augmented data if less available
        available_augmented = augmented_fed_zh + augmented_pboc_en
        if len(available_augmented) > target_augmented:
            # Sample to match ratio
            random.shuffle(available_augmented)
            available_augmented = available_augmented[:target_augmented]
        
        # Combine all data
        mixed = []
        
        # Add native data (mark as native)
        for record in native_fed:
            record['data_type'] = 'native'
            record['output_lang'] = 'en'
            mixed.append(record)
        
        for record in native_pboc:
            record['data_type'] = 'native'
            record['output_lang'] = 'zh'
            mixed.append(record)
        
        # Add augmented data
        for record in available_augmented:
            record['data_type'] = 'augmented'
            if record.get('augmentation_direction') == 'fed_to_zh':
                record['output_lang'] = 'zh'
            else:
                record['output_lang'] = 'en'
            mixed.append(record)
        
        # Shuffle to mix native and augmented
        random.shuffle(mixed)
        
        native_count = len(native_fed) + len(native_pboc)
        aug_count = len(available_augmented)
        total = native_count + aug_count
        
        print(f"[INFO] Mixed dataset: {native_count} native ({native_count/total*100:.1f}%) + "
              f"{aug_count} augmented ({aug_count/total*100:.1f}%) = {total} total")
        
        return mixed


# ==================== OUTPUT FORMATTER ====================

class ShareGPTFormatter:
    """Format mixed data to ShareGPT training format."""
    
    # Localized instruction templates
    INSTRUCTIONS = {
        "native_en": {
            "fed": "Summarize the following Federal Reserve policy statement:",
            "pboc": "Summarize the following PBOC policy statement:"
        },
        "native_zh": {
            "fed": "总结以下美联储政策声明：",
            "pboc": "总结以下中国人民银行政策声明："
        },
        "augmented_fed_to_zh": "以中国宏观经济学家视角，用中文分析以下美联储政策立场：",
        "augmented_pboc_to_en": "As a Wall Street analyst, analyze this PBOC policy stance:"
    }
    
    def format_record(self, record: Dict) -> Dict:
        """Convert a single record to ShareGPT format."""
        data_type = record.get('data_type', 'native')
        source = record.get('source', '').lower()
        output_lang = record.get('output_lang', 'en')
        
        # Determine instruction based on type and language
        if data_type == 'native':
            if output_lang == 'en':
                instruction = self.INSTRUCTIONS['native_en'].get(source, "Analyze this policy statement:")
            else:
                instruction = self.INSTRUCTIONS['native_zh'].get(source, "分析以下政策声明：")
            response_text = record.get('text', '')
        else:
            # Augmented data
            direction = record.get('augmentation_direction', '')
            if 'fed_to_zh' in direction:
                instruction = self.INSTRUCTIONS['augmented_fed_to_zh']
            else:
                instruction = self.INSTRUCTIONS['augmented_pboc_to_en']
            response_text = record.get('augmented_text', '')
        
        # Build ShareGPT conversation
        human_value = f"{instruction}\n\n{record.get('text', '')[:500]}"
        
        conversation = {
            "conversations": [
                {"from": "human", "value": human_value},
                {"from": "gpt", "value": response_text}
            ]
        }
        
        # Add metadata if configured
        conversation["metadata"] = {
            "source": source,
            "term": record.get('term', ''),
            "data_type": data_type,
            "output_lang": output_lang,
            "alignment_score": record.get('alignment_score', 0)
        }
        
        return conversation
    
    def format_all(self, records: List[Dict]) -> List[Dict]:
        """Format all records to ShareGPT format."""
        formatted = [self.format_record(r) for r in records]
        print(f"[INFO] Formatted {len(formatted)} records to ShareGPT format")
        return formatted
    
    def save_jsonl(self, records: List[Dict], output_path: str):
        """Save formatted records to JSONL file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        print(f"[INFO] Saved {len(records)} records to {output_path}")


# ==================== MAIN PIPELINE ====================

async def run_augmentation_pipeline(
    input_path: str,
    output_path: str,
    config: AugmentationConfig
):
    """
    Run the complete cross-lingual augmentation pipeline.
    
    Pipeline Steps:
    1. Load aligned corpus and extract policy evidence
    2. Segregate by source (FED/PBOC)
    3. Augment FED→ZH and PBOC→EN using LLM
    4. Mix native + augmented data (70/30 ratio)
    5. Format to ShareGPT and save
    """
    print("=" * 60)
    print("Cross-Lingual Augmentation Pipeline")
    print("=" * 60)
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"API Provider: {config.api_provider} ({config.model_name})")
    print(f"Augmentation Ratio: {config.augmentation_ratio * 100:.0f}%")
    print("=" * 60)
    
    # Step 1: Load data
    loader = DataLoader(input_path)
    cells = loader.load_aligned_corpus()
    fed_en, pboc_zh = loader.extract_policy_evidence(cells)
    
    if not fed_en and not pboc_zh:
        print("[ERROR] No policy evidence found in input data")
        return
    
    # Step 2: Augment cross-lingually
    augmenter = LLMAugmenter(config)
    
    print("\n[STAGE] Augmenting FED (EN) → Chinese analysis...")
    augmented_fed_zh = await augmenter.augment_batch(fed_en, "fed_to_zh")
    
    print("\n[STAGE] Augmenting PBOC (ZH) → English analysis...")
    augmented_pboc_en = await augmenter.augment_batch(pboc_zh, "pboc_to_en")
    
    # Step 3: Mix data
    print("\n[STAGE] Mixing native and augmented data...")
    mixer = MixingStrategy(config.augmentation_ratio)
    mixed_data = mixer.mix_data(fed_en, pboc_zh, augmented_fed_zh, augmented_pboc_en)
    
    # Step 4: Format and save
    print("\n[STAGE] Formatting to ShareGPT...")
    formatter = ShareGPTFormatter()
    formatted = formatter.format_all(mixed_data)
    formatter.save_jsonl(formatted, output_path)
    
    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print(f"Output file: {output_path}")
    print("=" * 60)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Cross-Lingual Augmentation for Financial LLM Training"
    )
    
    parser.add_argument(
        "--input", "-i",
        type=str,
        default="dataset/aligned_corpus.jsonl",
        help="Input JSONL file with aligned corpus"
    )
    
    parser.add_argument(
        "--output", "-o", 
        type=str,
        default="dataset/cross_lingual_training.jsonl",
        help="Output JSONL file in ShareGPT format"
    )
    
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "gemini"],
        default="openai",
        help="LLM API provider"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default="",
        help="API key (or set OPENAI_API_KEY / GEMINI_API_KEY env var)"
    )
    
    parser.add_argument(
        "--api-base",
        type=str,
        default="",
        help="Custom API base URL (optional)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="Model name (e.g., gpt-4o-mini, gemini-1.5-flash)"
    )
    
    parser.add_argument(
        "--ratio",
        type=float,
        default=0.3,
        help="Augmentation ratio (0.3 = 30%% augmented, 70%% native)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Concurrent API calls per batch"
    )
    
    args = parser.parse_args()
    
    # Resolve API key from args or environment
    api_key = args.api_key
    if not api_key:
        if args.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "")
        elif args.provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY", "")
    
    if not api_key:
        print("[ERROR] API key required. Provide via --api-key or environment variable.")
        print("  For OpenAI: set OPENAI_API_KEY")
        print("  For Gemini: set GEMINI_API_KEY")
        return
    
    # Build config
    config = AugmentationConfig(
        api_provider=args.provider,
        api_key=api_key,
        api_base_url=args.api_base,
        model_name=args.model,
        augmentation_ratio=args.ratio,
        batch_size=args.batch_size
    )
    
    # Resolve input path relative to project root
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / args.input
    output_path = project_root / args.output
    
    # Run pipeline
    asyncio.run(run_augmentation_pipeline(
        str(input_path),
        str(output_path),
        config
    ))


if __name__ == "__main__":
    main()
