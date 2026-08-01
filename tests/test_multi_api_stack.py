import pytest
from src.models.config import ApiProviderConfig, RewriterConfig, PipelineConfig
from src.rewriter.api_rewriter import ApiRewriter


def test_legacy_backwards_compatibility():
    """Verify legacy single api_url/api_model auto-constructs a working provider pool."""
    config = RewriterConfig(
        api_url="https://generativelanguage.googleapis.com/v1beta/openai",
        api_model="gemini-2.5-flash",
        timeout_seconds=5
    )
    assert len(config.providers) == 1
    assert config.providers[0].name == "legacy_api"
    assert config.providers[0].api_model == "gemini-2.5-flash"


def test_default_provider_stack_priority_order():
    """Verify default priority order: 1st OpenRouter -> 2nd Gemini -> 3rd Cerebras -> 4th Groq."""
    config = PipelineConfig()
    providers = config.rewriter.providers
    assert len(providers) == 4
    names = [p.name for p in providers]
    assert names == ["openrouter", "gemini", "cerebras", "groq"]
    priorities = [p.priority for p in providers]
    assert priorities == [1, 2, 3, 4]


def test_custom_api_key_top_priority(monkeypatch):
    """Verify that setting CUSTOM_API_KEY in environment auto-registers top priority custom provider."""
    monkeypatch.setenv("CUSTOM_API_KEY", "custom_secret_key_123")
    monkeypatch.setenv("CUSTOM_API_NAME", "my_custom_llm")
    monkeypatch.setenv("CUSTOM_API_URL", "https://my-custom-llm.ai/v1")
    monkeypatch.setenv("CUSTOM_API_MODEL", "custom-model-v1")

    config = PipelineConfig()
    providers = config.rewriter.providers
    assert providers[0].name == "my_custom_llm"
    assert providers[0].priority == 0
    assert providers[0].api_model == "custom-model-v1"


def test_api_rewriter_availability(monkeypatch):
    """Verify is_available() is True only when at least one provider has an active API key."""
    # Clear all keys
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    monkeypatch.delenv("CUSTOM_API_KEY", raising=False)

    providers = [
        ApiProviderConfig(name="groq", api_key_env="GROQ_API_KEY", api_url="http://fake", api_model="llama3", priority=4),
    ]
    rewriter = ApiRewriter(providers=providers)
    assert not rewriter.is_available()

    # Set key for Groq
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_12345")
    rewriter_with_key = ApiRewriter(providers=providers)
    assert rewriter_with_key.is_available()


def test_sequential_provider_failover(monkeypatch):
    """Verify that if Provider 1 fails, ApiRewriter transparently fails over to Provider 2."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key-openrouter")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_groq")

    providers = [
        ApiProviderConfig(name="failing_provider", api_key_env="OPENROUTER_API_KEY", api_url="http://invalid.domain.xyz/v1", api_model="model1", priority=1),
        ApiProviderConfig(name="working_provider", api_key_env="GROQ_API_KEY", api_url="https://generativelanguage.googleapis.com/v1beta/openai", api_model="gemini-2.5-flash", priority=2)
    ]

    rewriter = ApiRewriter(providers=providers)
    assert rewriter.is_available()
    assert rewriter.pool[0].config.name == "failing_provider"
    assert rewriter.pool[1].config.name == "working_provider"
