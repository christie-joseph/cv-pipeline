from ..ranker.skill_matcher import MatchResult
from ..models.resume import TailoredResume
from ..models.jd_profile import JDProfile


def generate_ats_report(jd_profile: JDProfile, match_result: MatchResult, resume: TailoredResume) -> str:
    match_pct = match_result.match_percentage
    rewriter_tier = resume.metadata.get("rewriter_tier", "Unknown")
    selected_exp_count = len(resume.selected_experiences)
    total_bullets = sum(len(e.selected_bullets) for e in resume.selected_experiences)

    lines = [
        "+----------------------------------------------+",
        "|              ATS MATCH REPORT                |",
        "+----------------------------------------------+",
        f"|  Overall Match Score:  {match_pct}%".ljust(47) + "|",
        "+----------------------------------------------+",
        "|  [+] Matched Skills                          |"
    ]

    for item, method in match_result.matched:
        lines.append(f"|    * {item:<16} ({method})".ljust(47) + "|")

    if not match_result.matched:
        lines.append("|    (None detected)".ljust(47) + "|")

    lines.append("+----------------------------------------------+")
    lines.append("|  [-] Missing Skills                          |")

    for item in match_result.missing[:8]:  # Limit top 8
        lines.append(f"|    * {item}".ljust(47) + "|")

    if not match_result.missing:
        lines.append("|    (None missing!)".ljust(47) + "|")

    lines.extend([
        "+----------------------------------------------+",
        f"|  Rewriter:    {rewriter_tier}".ljust(47) + "|",
        f"|  Experiences: {selected_exp_count} selected".ljust(47) + "|",
        f"|  Bullets:     {total_bullets} selected".ljust(47) + "|",
        "+----------------------------------------------+"
    ])

    return "\n".join(lines)
