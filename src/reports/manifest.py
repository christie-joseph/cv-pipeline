import hashlib
from datetime import datetime
from ..models.resume import TailoredResume
from ..models.config import PipelineConfig


def generate_manifest(jd_text: str, resume: TailoredResume, config: PipelineConfig) -> str:
    jd_hash = hashlib.sha256(jd_text.encode("utf-8")).hexdigest()[:16]
    timestamp = datetime.now().isoformat(timespec="seconds")
    rewriter_tier = resume.metadata.get("rewriter_tier", "Unknown")

    exp_details = []
    for e in resume.selected_experiences:
        b_ids = ",".join(b.bullet.id for b in e.selected_bullets)
        exp_details.append(f"  {e.experience.id} [{e.composite_score}] -> bullets: ({b_ids})")

    lines = [
        "----------- REPRODUCIBILITY MANIFEST -----------",
        f"Timestamp:            {timestamp}",
        f"JD SHA-256 Hash:      {jd_hash}",
        f"Rewriter Tier Used:   {rewriter_tier}",
        f"Embedding Model:      {config.embedding_model}",
        "",
        "Config Snapshot:",
        f"  max_experiences: {config.max_experiences}, max_bullets: {config.max_bullets_per_experience}",
        f"  min_similarity: {config.minimum_similarity}, mmr_lambda: {config.mmr_lambda}",
        "",
        "Selected Experiences & Bullets:"
    ] + exp_details + [
        "",
        f"Selected Skills: {', '.join(resume.selected_skills)}",
        "------------------------------------------------"
    ]

    return "\n".join(lines)
