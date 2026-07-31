from src.pipeline import Pipeline
from src.models.config import PipelineConfig


def test_pipeline_e2e():
    config = PipelineConfig.load_from_yaml("config.yaml")
    config.output.compile_pdf = False  # Pure in-memory LaTeX string test

    pipeline = Pipeline(config=config)
    jd_text = """
    Looking for a Senior Java Backend Engineer with experience in Kafka, Redis, and Spring Boot.
    Must have knowledge of distributed systems and Docker.
    """

    result = pipeline.run(jd_text=jd_text, company_profile_name="google")
    assert result.latex_string
    assert "\\begin{document}" in result.latex_string
    assert result.ats_report
    assert result.diff_report
    assert result.manifest
