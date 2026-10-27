import pytest
from pathlib import Path
from src.pipeline import Pipeline
from src.models.config import PipelineConfig


def test_offline_pipeline_execution(monkeypatch):
    """Verifies pipeline runs 100% offline with zero network sockets without throwing."""
    import socket

    def guarded_connect(*args, **kwargs):
        raise OSError("Network access disabled in offline test")

    monkeypatch.setattr(socket, "create_connection", guarded_connect)

    jd_path = Path("jobs/benchmarks/01_backend_distributed.txt")
    if not jd_path.exists():
        pytest.skip("Benchmark file missing")

    jd_text = jd_path.read_text(encoding="utf-8")
    cfg = PipelineConfig(offline=True)
    cfg.output.open_pdf = False
    cfg.output.compile_pdf = False  # Keep test fast and memory-only

    pipeline = Pipeline(config=cfg)
    assert pipeline.config.offline is True
    assert pipeline.embedding_model is None  # FastEmbed skipped in offline mode

    result = pipeline.run(jd_text=jd_text)

    assert result is not None
    assert result.latex_string is not None
    assert len(result.latex_string) > 100
    assert result.ats_report is not None
    assert "ATS MATCH REPORT" in result.ats_report
