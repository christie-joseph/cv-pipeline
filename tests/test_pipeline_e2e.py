from pathlib import Path
from src.pipeline import Pipeline
from src.models.config import PipelineConfig

project_root = Path(__file__).resolve().parent.parent


def test_pipeline_e2e():
    config_path = str(project_root / "config.yaml")
    config = PipelineConfig.load_from_yaml(config_path)
    config.output.compile_pdf = False

    pipeline = Pipeline(config=config)
    jd_text = """
    Looking for a Senior Java Backend Engineer with experience in Kafka, Redis, and Spring Boot.
    Must have knowledge of distributed systems and Docker.
    """

    result = pipeline.run(jd_text=jd_text, company_profile_name="google")
    assert result.latex_string
    assert "\\begin{document}" in result.latex_string
    assert "\\end{document}" in result.latex_string
    assert "\\resumeSubHeadingListStart" in result.latex_string
    assert "\\resumeItem" in result.latex_string
    assert "\\section{Experience}" in result.latex_string

    assert result.ats_report
    assert "ATS" in result.ats_report.upper() or "MATCH" in result.ats_report.upper()

    assert result.diff_report
    assert "SELECTED EXPERIENCES:" in result.diff_report
    assert "BULLET CHANGES:" in result.diff_report

    assert result.manifest
    assert "REPRODUCIBILITY MANIFEST" in result.manifest
    assert "JD SHA-256 Hash:" in result.manifest
    assert "Rewriter Tier Used:" in result.manifest
    assert "Selected Skills:" in result.manifest
