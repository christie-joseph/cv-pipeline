from typing import List
from ..models.experience import Experience
from ..models.resume import TailoredResume


def generate_diff_report(all_experiences: List[Experience], resume: TailoredResume) -> str:
    selected_ids = {e.experience.id for e in resume.selected_experiences}
    
    lines = [
        "--------------- RESUME DIFF ---------------",
        "",
        "SELECTED EXPERIENCES:"
    ]

    for i, sel_exp in enumerate(resume.selected_experiences, 1):
        exp = sel_exp.experience
        lines.append(f"  [{i}] {exp.company:<16} -> \"{sel_exp.selected_title}\" (score: {sel_exp.composite_score})")

    lines.append("")
    lines.append("EXCLUDED EXPERIENCES:")

    excluded = [e for e in all_experiences if e.id not in selected_ids]
    for exp in excluded:
        lines.append(f"  [-] {exp.company:<16} (excluded by threshold/limit)")

    if not excluded:
        lines.append("  (None)")

    lines.append("")
    lines.append("BULLET CHANGES:")

    for sel_exp in resume.selected_experiences:
        lines.append(f"  * {sel_exp.experience.company}:")
        for sel_b in sel_exp.selected_bullets:
            bullet_id = sel_b.bullet.id
            preview = sel_b.rewritten_text[:50] + "..." if len(sel_b.rewritten_text) > 50 else sel_b.rewritten_text
            lines.append(f"    [+] [{bullet_id}] \"{preview}\" (rel: {sel_b.relevance_score})")

    lines.append("")
    lines.append(f"SELECTED SKILLS: {', '.join(resume.selected_skills)}")
    lines.append("-------------------------------------------")

    return "\n".join(lines)
