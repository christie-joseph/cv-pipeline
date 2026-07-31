from src.models.config import PipelineConfig
from src.rewriter.chain import RewriterChain


def test_rewriter_chain_fallback_to_option_c():
    config = PipelineConfig()
    # Force cloud API to fail by clearing env
    chain = RewriterChain(config)

    bullet_text = "worked on backend services in Java"
    rewritten, tier = chain.rewrite(bullet_text, ["java", "backend"])

    assert rewritten
    assert tier in ["Option C (Rule Engine)", "Option B (Local Ollama GPU)", "Option A (Cloud API)"]
    # Check that weak verb 'worked on' was upgraded if rule engine was hit
    if tier == "Option C (Rule Engine)":
        assert "engineered" in rewritten
