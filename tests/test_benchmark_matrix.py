import re
import pytest
from pathlib import Path
from src.pipeline import Pipeline
from src.models.config import PipelineConfig


def test_benchmark_scoring_monotonicity():
    """
    Asserts relative scoring monotonicity:
    Aligned backend/cloud engineering roles must significantly outscore
    an entirely irrelevant sales/marketing role.
    """
    benchmarks_dir = Path("jobs/benchmarks")
    if not benchmarks_dir.exists():
        pytest.skip("Benchmark directory missing")

    cfg = PipelineConfig(offline=True)
    cfg.output.open_pdf = False
    cfg.output.compile_pdf = False
    pipeline = Pipeline(config=cfg)

    backend_text = (benchmarks_dir / "01_backend_distributed.txt").read_text(encoding="utf-8")
    marketing_text = (benchmarks_dir / "06_marketing_irrelevant.txt").read_text(encoding="utf-8")

    res_backend = pipeline.run(backend_text)
    res_marketing = pipeline.run(marketing_text)

    # Extract score from ats_report output: "Overall Match:   65.0%"
    match_backend = re.search(r"Overall Match:\s+([\d\.]+)%", res_backend.ats_report)
    match_marketing = re.search(r"Overall Match:\s+([\d\.]+)%", res_marketing.ats_report)

    assert match_backend is not None
    assert match_marketing is not None

    score_backend = float(match_backend.group(1))
    score_marketing = float(match_marketing.group(1))

    # 1. Monotonicity: Aligned backend role must outscore marketing role by a wide margin
    assert score_backend > score_marketing
    assert score_backend >= 50.0

    # 2. Zero-Hallucination check: Marketing role match must be very low
    assert score_marketing <= 25.0
