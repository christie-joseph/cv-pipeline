from ..ranker.skill_matcher import MatchResult
from ..models.resume import TailoredResume
from ..models.jd_profile import JDProfile


def generate_ats_report(jd_profile: JDProfile, match_result: MatchResult, resume: TailoredResume) -> str:
    match_pct = match_result.match_percentage
    rewriter_tier = resume.metadata.get("rewriter_tier", "Unknown")
    selected_exp_count = len(resume.selected_experiences)
    total_bullets = sum(len(e.selected_bullets) for e in resume.selected_experiences)

    role_str = (jd_profile.role[:28] + "..") if jd_profile.role and len(jd_profile.role) > 30 else (jd_profile.role or "Unspecified")
    seniority_str = jd_profile.seniority or "Standard"

    lines = [
        "+----------------------------------------------+",
        "|              ATS MATCH REPORT                |",
        "+----------------------------------------------+",
        f"|  Role Target:    {role_str:<27}".ljust(47) + "|",
        f"|  Seniority:      {seniority_str:<27}".ljust(47) + "|",
        f"|  Overall Score:  {match_pct}%".ljust(47) + "|",
        "+----------------------------------------------+",
        "|  [+] Matched Skills                          |"
    ]

    for item, method in match_result.matched:
        # Truncate item if too long to prevent box overflow
        clean_item = (item[:15] + "..") if len(item) > 17 else item
        clean_method = (method[:14] + "..") if len(method) > 16 else method
        lines.append(f"|    * {clean_item:<17} ({clean_method})".ljust(47) + "|")

    if not match_result.matched:
        lines.append("|    (None detected)".ljust(47) + "|")

    lines.append("+----------------------------------------------+")
    lines.append("|  [-] Missing Skills                          |")

    for item in match_result.missing[:8]:  # Limit top 8
        clean_item = (item[:35] + "..") if len(item) > 37 else item
        lines.append(f"|    * {clean_item}".ljust(47) + "|")

    if not match_result.missing:
        lines.append("|    (None missing!)".ljust(47) + "|")

    lines.extend([
        "+----------------------------------------------+",
        f"|  Rewriter:    {rewriter_tier[:30]}".ljust(47) + "|",
        f"|  Experiences: {selected_exp_count} selected".ljust(47) + "|",
        f"|  Bullets:     {total_bullets} selected".ljust(47) + "|",
        "+----------------------------------------------+"
    ])

    return "\n".join(lines)
