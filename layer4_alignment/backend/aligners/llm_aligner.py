"""
LLM Semantic Aligner

Uses Gemini/GPT-4 to semantically judge relevance between
terms and candidate texts.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional

from .base_aligner import BaseAligner, AlignmentResult


class LLMAligner(BaseAligner):
    """
    Aligns candidates using LLM semantic judgment.
    
    Sends batches of candidates to Gemini/GPT-4 and asks for
    relevance scoring. Most accurate but has API costs.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self.provider = config.get("provider", "gemini")
        self.model_name = config.get("model", "gemini-1.5-flash")
        self.temperature = config.get("temperature", 0.1)
        self.max_tokens = config.get("max_tokens", 1000)
        self.batch_size = config.get("batch_size", 10)
        self.api_key_env = config.get("api_key_env", "GEMINI_API_KEY")
        
        self._client = None
        self._initialized = False
    
    def _init_client(self):
        """Initialize the LLM client."""
        if self._initialized:
            return
        
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            print(f"[WARN] LLMAligner: {self.api_key_env} not set, will return empty results")
            self._initialized = True
            return
        
        if self.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self._client = genai.GenerativeModel(self.model_name)
                self._initialized = True
                print(f"[INFO] LLMAligner initialized with {self.model_name}")
            except ImportError:
                print("[WARN] google-generativeai not installed, LLM alignment disabled")
                self._initialized = True
        
        elif self.provider == "openai":
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=api_key)
                self._initialized = True
                print(f"[INFO] LLMAligner initialized with OpenAI {self.model_name}")
            except ImportError:
                print("[WARN] openai not installed, LLM alignment disabled")
                self._initialized = True
    
    async def align(
        self,
        term: str,
        term_definition: str,
        candidates: List[Dict[str, Any]],
        layer: str
    ) -> List[AlignmentResult]:
        """
        Score candidates using LLM semantic judgment.
        
        Processes candidates in batches to reduce API calls.
        """
        self._init_client()
        
        if not self._client or not candidates:
            return []
        
        results = []
        
        # Process in batches
        for i in range(0, len(candidates), self.batch_size):
            batch = candidates[i:i + self.batch_size]
            batch_results = await self._process_batch(term, term_definition, batch, layer)
            results.extend(batch_results)
            
            # Rate limiting
            if i + self.batch_size < len(candidates):
                await asyncio.sleep(0.5)
        
        return results
    
    async def _process_batch(
        self,
        term: str,
        term_definition: str,
        batch: List[Dict[str, Any]],
        layer: str
    ) -> List[AlignmentResult]:
        """Process a single batch of candidates."""
        
        prompt = self._build_prompt(term, term_definition, batch, layer)
        
        try:
            if self.provider == "gemini":
                response = await asyncio.to_thread(
                    self._client.generate_content,
                    prompt,
                    generation_config={
                        "temperature": self.temperature,
                        "max_output_tokens": self.max_tokens
                    }
                )
                response_text = response.text
            
            elif self.provider == "openai":
                response = await self._client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                response_text = response.choices[0].message.content
            
            else:
                return []
            
            # Parse response
            return self._parse_response(response_text, batch)
        
        except Exception as e:
            print(f"[WARN] LLM API error: {e}")
            return []
    
    def _build_prompt(
        self,
        term: str,
        term_definition: str,
        batch: List[Dict[str, Any]],
        layer: str
    ) -> str:
        """Build the LLM prompt for alignment scoring."""
        
        layer_desc = "policy paragraph" if layer == "policy" else "news article"
        
        prompt = f"""You are an expert economist. Your task is to rate how relevant each {layer_desc} is to the economic concept "{term}".

**Concept Definition:**
{term_definition[:500]}

**Scoring Guidelines:**
- 0.9-1.0: Directly discusses or defines this concept
- 0.7-0.9: Strongly related, mentions the concept in context
- 0.5-0.7: Somewhat related, touches on related themes
- 0.3-0.5: Weakly related, tangential connection
- 0.0-0.3: Not related or only superficially mentions keywords

**Texts to evaluate:**
"""
        
        for i, candidate in enumerate(batch):
            text = candidate.get('text', candidate.get('title', ''))[:300]
            prompt += f"\n[{i}] {text}\n"
        
        prompt += """
**Response Format:**
Return a JSON array with your ratings. Each item must have:
- "index": the text index number
- "score": relevance score (0.0 to 1.0)
- "reason": brief explanation (max 20 words)

Example: [{"index": 0, "score": 0.85, "reason": "Directly discusses inflation trends"}]

**Your JSON response:**"""
        
        return prompt
    
    def _parse_response(
        self,
        response_text: str,
        batch: List[Dict[str, Any]]
    ) -> List[AlignmentResult]:
        """Parse LLM response into AlignmentResults."""
        
        results = []
        
        try:
            # Extract JSON from response
            text = response_text.strip()
            
            # Find JSON array
            start = text.find('[')
            end = text.rfind(']') + 1
            
            if start >= 0 and end > start:
                json_str = text[start:end]
                scores = json.loads(json_str)
                
                for item in scores:
                    idx = item.get('index', -1)
                    if 0 <= idx < len(batch):
                        results.append(AlignmentResult(
                            candidate_id=batch[idx]['id'],
                            score=float(item.get('score', 0)),
                            method="llm_semantic",
                            reason=item.get('reason')
                        ))
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[WARN] Failed to parse LLM response: {e}")
        
        return results
