from src.models.config import PipelineConfig
from src.rewriter.chain import RewriterChain


def test_rewriter_chain_fallback_no_keys(monkeypatch):
    """Verify that complete absence of API keys causes zero blocking errors and falls back smoothly."""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    monkeypatch.delenv("CUSTOM_API_KEY", raising=False)

    config = PipelineConfig()
    chain = RewriterChain(config)

    bullet_text = "worked on backend services in Java"
    rewritten, tier = chain.rewrite(bullet_text, ["java", "backend"])

    assert rewritten
    assert tier in ["Option C (Rule Engine)", "Option B (Local Ollama GPU)"]
    if tier == "Option C (Rule Engine)":
        assert "engineered" in rewritten


def test_rewriter_chain_fallback_whitespace_keys(monkeypatch):
    """Verify that whitespace-only keys ('   ') do not cause blocking errors."""
    monkeypatch.setenv("LLM_API_KEY", "   ")
    monkeypatch.setenv("GEMINI_API_KEY", "   ")
    monkeypatch.setenv("GROQ_API_KEY", " \t\n ")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")

    config = PipelineConfig()
    chain = RewriterChain(config)

    bullet_text = "worked on backend services in Java"
    rewritten, tier = chain.rewrite(bullet_text, ["java", "backend"])

    assert rewritten
    assert tier in ["Option C (Rule Engine)", "Option B (Local Ollama GPU)"]


def test_rewriter_chain_fallback_invalid_key_exception(monkeypatch):
    """Verify that invalid API keys triggering network/auth exceptions fail over smoothly to Tier B/C."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "invalid_revoked_key_999")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)

    config = PipelineConfig()
    chain = RewriterChain(config)

    bullet_text = "worked on backend services in Java"
    # Execution should NOT crash or block; it falls through smoothly
    rewritten, tier = chain.rewrite(bullet_text, ["java", "backend"])

    assert rewritten
    assert tier in ["Option C (Rule Engine)", "Option B (Local Ollama GPU)"]
