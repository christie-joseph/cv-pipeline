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
        if not self.rewriter_cfg.enabled:
            return bullet_text, "Disabled"

        prompt = self.config.rewriter_prompt

        # Tier A: Cloud LLM API Pool
        if self.option_a.is_available():
            try:
                res, provider_name = self.option_a.rewrite(bullet_text, jd_keywords, prompt)
                if _validate_rewrite_guardrails(bullet_text, res):
                    return res, f"Option A (Cloud API: {provider_name})"
                else:
                    logger.warning("Option A failed guardrails. Falling back to Option B...")
            except Exception as e:
                logger.warning(f"Option A Cloud API pool failed: {e}. Falling back to Option B...")

        # Tier B: Local Ollama GPU/CPU
        if self.option_b.is_available():
            try:
                res = self.option_b.rewrite(bullet_text, jd_keywords, prompt)
                if _validate_rewrite_guardrails(bullet_text, res):
                    return res, "Option B (Local Ollama GPU)"
                else:
                    logger.warning("Option B failed guardrails. Falling back to Option C...")
            except Exception as e:
                logger.warning(f"Option B (Ollama) failed: {e}. Falling back to Option C...")

        # Tier C: Deterministic Rule Engine (Inherently safe from LLM hallucination)
        res = self.option_c.rewrite(bullet_text, jd_keywords, prompt)
        return res, "Option C (Rule Engine)"
