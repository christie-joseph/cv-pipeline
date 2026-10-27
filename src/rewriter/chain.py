import re
import logging
from typing import List, Tuple, Optional, Dict
from rich import print as rprint
from ..models.config import PipelineConfig
from .api_rewriter import ApiRewriter
from .ollama_rewriter import OllamaRewriter
from .rule_rewriter import RuleRewriter

logger = logging.getLogger(__name__)


def _extract_metrics(text: str) -> List[str]:
    """Extract numeric metrics, percentages, latencies, currency, and scales."""
    matches = re.findall(
        r"[\$£€]?\b\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:%|x|ms|s|gb|tb|mb|pb|k|m|b))\b|[\$£€]\d+(?:,\d{3})*(?:\.\d+)?\b|\b\d+(?:,\d{3})*(?:\.\d+)?%|\b\d+(?:,\d{3})+(?:\.\d+)?\b|\b\d+(?:\.\d+)?\b",
        text,
        re.IGNORECASE
    )
    normalized = []
    for m in matches:
        clean = re.sub(r",", "", m.strip().lower())
        clean = re.sub(r"\s+", "", clean)
        normalized.append(clean)
    return normalized


def _validate_rewrite_guardrails(original: str, rewritten: str) -> bool:
    """Strict check to ensure LLM didn't hallucinate/drop metrics or expand excessively."""
    orig_len = len(original.strip())
    rewritten_len = len(rewritten.strip())
    if orig_len > 0:
        ratio = rewritten_len / orig_len
        if ratio < 0.5 or ratio > 2.0:
            logger.warning(f"Guardrail failed: length ratio {ratio:.2f} out of bounds (0.5 - 2.0).")
            return False

    orig_metrics = _extract_metrics(original)
    rewritten_metrics = _extract_metrics(rewritten)

    # 1. Metric retention: all metrics in original must exist in rewritten
    for m in orig_metrics:
        if m not in rewritten_metrics:
            num_only = re.sub(r"[^\d.]", "", m)
            if not any(num_only in rm for rm in rewritten_metrics):
                logger.warning(f"Guardrail failed: dropped metric '{m}'.")
                return False

    # 2. Hallucination detection: no new metrics invented by LLM
    for rm in rewritten_metrics:
        if rm not in orig_metrics:
            num_only = re.sub(r"[^\d.]", "", rm)
            if not any(num_only in om for om in orig_metrics):
                logger.warning(f"Guardrail failed: hallucinated new metric '{rm}'.")
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

        # Option C: Rule-Based Fallback (Deterministic, Upgraded)
        self.option_c = RuleRewriter()

    def rewrite(
        self,
        bullet_text: str,
        jd_keywords: List[str],
        bullet_tags: Optional[List[str]] = None,
        keyword_scores: Optional[Dict[str, float]] = None
    ) -> Tuple[str, str]:
        """Runs bullet text through fallback chain A -> B -> C. Returns (rewritten_text, tier_name)."""
        tags_list = [bullet_tags] if bullet_tags else None
        res, tiers = self.rewrite_batch(
            bullets=[bullet_text],
            jd_keywords=jd_keywords,
            bullets_tags=tags_list,
            keyword_scores=keyword_scores
        )
        return res[0], tiers[0]

    def rewrite_batch(
        self,
        bullets: List[str],
        jd_keywords: List[str],
        bullets_tags: Optional[List[List[str]]] = None,
        keyword_scores: Optional[Dict[str, float]] = None
    ) -> Tuple[List[str], List[str]]:
        """Runs list of bullets through fallback chain in batch mode. Returns (rewritten_texts, tier_names)."""
        if not bullets:
            return [], []

        if not self.rewriter_cfg.enabled:
            return bullets, ["Disabled"] * len(bullets)

        prompt = self.config.rewriter_prompt

        # Tier A: Cloud LLM API Pool Batch
        if self.option_a.is_available():
            try:
                rprint("[bold cyan][*] Attempting Rewriter Option A (Cloud LLM API Pool)...[/bold cyan]")
                res_list, provider_name = self.option_a.rewrite_batch(bullets, jd_keywords, prompt)
                
                final_results = []
                final_tiers = []
                failed_indices = []
                
                for idx, (orig, rewritten) in enumerate(zip(bullets, res_list)):
                    if _validate_rewrite_guardrails(orig, rewritten):
                        final_results.append(rewritten)
                        final_tiers.append(f"Option A (Cloud API: {provider_name})")
                    else:
                        rprint(f"[yellow][!] Option A bullet {idx+1} failed guardrails. Falling back to Option B/C...[/yellow]")
                        logger.warning(f"Option A bullet {idx+1} failed guardrails. Falling back...")
                        failed_indices.append(idx)
                        final_results.append(None)
                        final_tiers.append(None)
                
                if not failed_indices:
                    return final_results, final_tiers
                
                for idx in failed_indices:
                    orig = bullets[idx]
                    b_tags = bullets_tags[idx] if bullets_tags and idx < len(bullets_tags) else None
                    fallback_text, fallback_tier = self._rewrite_single_fallback(
                        orig, jd_keywords, prompt, bullet_tags=b_tags, keyword_scores=keyword_scores
                    )
                    final_results[idx] = fallback_text
                    final_tiers[idx] = fallback_tier
                    
                return final_results, final_tiers

            except Exception as e:
                rprint(f"[yellow][!] Option A (Cloud API Pool) failed: {e}. Falling back to Option B/C...[/yellow]")
                logger.warning(f"Option A Cloud API pool batch failed: {e}. Falling back to Option B/C...")

        # Fallback for all bullets if Option A fails
        results = []
        tiers = []
        for idx, b in enumerate(bullets):
            b_tags = bullets_tags[idx] if bullets_tags and idx < len(bullets_tags) else None
            res_text, res_tier = self._rewrite_single_fallback(
                b, jd_keywords, prompt, bullet_tags=b_tags, keyword_scores=keyword_scores
            )
            results.append(res_text)
            tiers.append(res_tier)
        return results, tiers

    def _rewrite_single_fallback(
        self,
        bullet_text: str,
        jd_keywords: List[str],
        prompt: str,
        bullet_tags: Optional[List[str]] = None,
        keyword_scores: Optional[Dict[str, float]] = None
    ) -> Tuple[str, str]:
        """Fallback for a single bullet through Option B -> Option C."""
        if self.option_b.is_available():
            try:
                rprint("[cyan][*] Attempting Rewriter Option B (Local Ollama)...[/cyan]")
                res = self.option_b.rewrite(bullet_text, jd_keywords, prompt)
                if _validate_rewrite_guardrails(bullet_text, res):
                    rprint("[green][+] Option B (Local Ollama) succeeded![/green]")
                    return res, "Option B (Local Ollama GPU)"
                else:
                    rprint("[yellow][!] Option B failed guardrails. Falling back to Option C (Rule Engine)...[/yellow]")
                    logger.warning("Option B failed guardrails. Falling back to Option C...")
            except Exception as e:
                rprint(f"[yellow][!] Option B (Ollama) failed: {e}. Falling back to Option C (Rule Engine)...[/yellow]")
                logger.warning(f"Option B (Ollama) failed: {e}. Falling back to Option C...")

        rprint("[cyan][*] Using Rewriter Option C (Deterministic Rule Engine fallback)...[/cyan]")
        res = self.option_c.rewrite(
            bullet_text,
            jd_keywords,
            prompt,
            bullet_tags=bullet_tags,
            keyword_scores=keyword_scores
        )
        return res, "Option C (Rule Engine)"
