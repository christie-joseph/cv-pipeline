import logging
from typing import List, Tuple
from ..models.config import PipelineConfig
from .api_rewriter import ApiRewriter
from .ollama_rewriter import OllamaRewriter
from .rule_rewriter import RuleRewriter

logger = logging.getLogger(__name__)


import re

def _validate_rewrite_guardrails(original: str, rewritten: str) -> bool:
    """Strict check to ensure LLM didn't hallucinate/drop metrics or expand excessively."""
    # 1. Length bounding (between 0.5x and 2.5x of original)
    orig_len = len(original.strip())
    rewritten_len = len(rewritten.strip())
    if orig_len > 0:
        ratio = rewritten_len / orig_len
        if ratio < 0.5 or ratio > 2.5:
            logger.warning(f"Guardrail failed: length ratio {ratio:.2f} out of bounds (0.5 - 2.5).")
            return False

    # 2. Metric retention (extract numbers like 30%, 50ms, 5)
    orig_metrics = re.findall(r"\b\d+(?:\.\d+)?%?\b", original)
    for m in orig_metrics:
        if m not in rewritten:
            logger.warning(f"Guardrail failed: dropped metric '{m}'.")
            return False

    return True


class RewriterChain:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.rewriter_cfg = config.rewriter

        # Option A: Stacked Cloud LLM API Pool (Gemini, Groq, OpenRouter, Cerebras)
        self.option_a = ApiRewriter(
            providers=self.rewriter_cfg.providers
        )

        # Option B: Local Ollama GPU/CPU
        self.option_b = OllamaRewriter(
            model_name=self.rewriter_cfg.ollama_model,
            timeout_seconds=self.rewriter_cfg.ollama_timeout
        )

        # Option C: Rule-Based Fallback (Guaranteed)
        self.option_c = RuleRewriter()

    def rewrite(self, bullet_text: str, jd_keywords: List[str]) -> Tuple[str, str]:
        """Runs bullet text through fallback chain A -> B -> C. Returns (rewritten_text, tier_name)."""
        res, tiers = self.rewrite_batch([bullet_text], jd_keywords)
        return res[0], tiers[0]

    def rewrite_batch(self, bullets: List[str], jd_keywords: List[str]) -> Tuple[List[str], List[str]]:
        """Runs list of bullets through fallback chain in batch mode. Returns (rewritten_texts, tier_names)."""
        if not bullets:
            return [], []

        if not self.rewriter_cfg.enabled:
            return bullets, ["Disabled"] * len(bullets)

        prompt = self.config.rewriter_prompt

        # Tier A: Cloud LLM API Pool Batch
        if self.option_a.is_available():
            try:
                res_list, provider_name = self.option_a.rewrite_batch(bullets, jd_keywords, prompt)
                
                # Check guardrails per bullet
                final_results = []
                final_tiers = []
                failed_indices = []
                
                for idx, (orig, rewritten) in enumerate(zip(bullets, res_list)):
                    if _validate_rewrite_guardrails(orig, rewritten):
                        final_results.append(rewritten)
                        final_tiers.append(f"Option A (Cloud API: {provider_name})")
                    else:
                        logger.warning(f"Option A bullet {idx+1} failed guardrails. Falling back...")
                        failed_indices.append(idx)
                        final_results.append(None)
                        final_tiers.append(None)
                
                # If all succeeded, return immediately
                if not failed_indices:
                    return final_results, final_tiers
                
                # For any failed bullets, process them individually through Option B or C
                for idx in failed_indices:
                    orig = bullets[idx]
                    fallback_text, fallback_tier = self._rewrite_single_fallback(orig, jd_keywords, prompt)
                    final_results[idx] = fallback_text
                    final_tiers[idx] = fallback_tier
                    
                return final_results, final_tiers

            except Exception as e:
                logger.warning(f"Option A Cloud API pool batch failed: {e}. Falling back to Option B/C...")

        # Fallback for all bullets if Option A fails
        results = []
        tiers = []
        for b in bullets:
            res_text, res_tier = self._rewrite_single_fallback(b, jd_keywords, prompt)
            results.append(res_text)
            tiers.append(res_tier)
        return results, tiers

    def _rewrite_single_fallback(self, bullet_text: str, jd_keywords: List[str], prompt: str) -> Tuple[str, str]:
        """Fallback for a single bullet through Option B -> Option C."""
        if self.option_b.is_available():
            try:
                res = self.option_b.rewrite(bullet_text, jd_keywords, prompt)
                if _validate_rewrite_guardrails(bullet_text, res):
                    return res, "Option B (Local Ollama GPU)"
                else:
                    logger.warning("Option B failed guardrails. Falling back to Option C...")
            except Exception as e:
                logger.warning(f"Option B (Ollama) failed: {e}. Falling back to Option C...")

        res = self.option_c.rewrite(bullet_text, jd_keywords, prompt)
        return res, "Option C (Rule Engine)"
