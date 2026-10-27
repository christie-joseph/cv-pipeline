import re
from typing import Optional, Dict, List
from ..ranker.skill_matcher import MatchResult
from ..models.resume import TailoredResume
from ..models.jd_profile import JDProfile
from ..ranker.faang_scorer import STRONG_ACTION_VERBS, WEAK_VERBS
from ..ranker.cliche_detector import ClicheDetector


def generate_ats_report(
    jd_profile: JDProfile,
    match_result: MatchResult,
    resume: TailoredResume,
    keyword_scores: Optional[Dict[str, float]] = None
) -> str:
    match_pct = match_result.match_percentage
    rewriter_tier = resume.metadata.get("rewriter_tier", "Unknown")
    selected_exp_count = len(resume.selected_experiences)
    all_bullets = [b for e in resume.selected_experiences for b in e.selected_bullets]
    total_bullets = len(all_bullets)

    cliche_detector = ClicheDetector()
    cliche_matches = []

    # 1. Compute bullet quality signals
    metric_count = 0
    strong_verb_count = 0
    weak_verb_count = 0

    for sel_b in all_bullets:
        b_text = sel_b.rewritten_text or sel_b.bullet.text
        # Metrics check
        if re.search(r"\b\d+(?:\.\d+)?%?\b|\b\d+[KMB]\b|\b\d+\+?\s*(users|requests|events|gb|tb|ms|s)\b", b_text, re.IGNORECASE):
            metric_count += 1

        # Action verb check
        first_word = re.sub(r'[^a-z]', '', b_text.lower().split()[0]) if b_text.split() else ""
        if first_word in STRONG_ACTION_VERBS:
            strong_verb_count += 1
        elif first_word in WEAK_VERBS:
            weak_verb_count += 1

        # Cliché & overused anti-pattern check
        c_found = cliche_detector.detect(b_text)
        if c_found:
            cliche_matches.extend(c_found)

    # 2. Compute Keyword Density Score
    resume_full_text = " ".join([b.rewritten_text or b.bullet.text for b in all_bullets]).lower()
    for proj in resume.projects:
        resume_full_text += " " + " ".join(proj.bullets).lower() + " " + " ".join(proj.tech_stack).lower()

    kw_scores = keyword_scores or getattr(jd_profile, "keyword_scores", {}) or {}
    covered_val = 0.0
    total_val = 0.0

    top_keywords = jd_profile.keywords[:15] if jd_profile.keywords else []
    for kw in top_keywords:
        wt = kw_scores.get(kw, 1.0)
        total_val += wt
        pattern = r"\b" + re.escape(kw.lower()) + r"\b" if re.match(r"^\w", kw) else re.escape(kw.lower())
        if re.search(pattern, resume_full_text):
            covered_val += wt

    keyword_density = round((covered_val / total_val) * 100, 1) if total_val > 0 else 100.0

    # 3. Format Card Box
    role_str = (jd_profile.role[:28] + "..") if jd_profile.role and len(jd_profile.role) > 30 else (jd_profile.role or "Unspecified")
    seniority_str = jd_profile.seniority or "Standard"

    width = 50
    border = "+" + "-" * (width - 2) + "+"

    def fmt_row(content: str) -> str:
        truncated = content[:width - 4]
        return f"| {truncated:<{width - 4}} |"

    req_tot = len(match_result.required_matched) + len(match_result.required_missing)
    pref_tot = len(match_result.preferred_matched) + len(match_result.preferred_missing)

    lines = [
        border,
        fmt_row("              ATS MATCH REPORT"),
        border,
        fmt_row(f"Role Target:     {role_str}"),
        fmt_row(f"Seniority:       {seniority_str}"),
        fmt_row(f"Overall Match:   {match_pct}%"),
    ]

    if req_tot > 0 and pref_tot > 0:
        lines.append(fmt_row(f"  - Required:    {len(match_result.required_matched)}/{req_tot} matched"))
        lines.append(fmt_row(f"  - Preferred:   {len(match_result.preferred_matched)}/{pref_tot} matched"))

    lines.extend([
        fmt_row(f"Keyword Density: {keyword_density}%"),
        border,
        fmt_row("[+] Matched Skills")
    ])

    for item, method in match_result.matched:
        clean_item = (item[:16] + "..") if len(item) > 18 else item
        clean_method = (method[:14] + "..") if len(method) > 16 else method
        lines.append(fmt_row(f"  * {clean_item:<18} ({clean_method})"))

    if not match_result.matched:
        lines.append(fmt_row("  (None detected)"))

    lines.append(border)

    # Missing skills breakdown
    if match_result.required_missing:
        lines.append(fmt_row("[-] Missing Critical Skills (Required)"))
        for item in match_result.required_missing[:5]:
            clean_item = (item[:38] + "..") if len(item) > 40 else item
            lines.append(fmt_row(f"  * {clean_item}"))
        if match_result.preferred_missing:
            lines.append(fmt_row("[-] Missing Bonus Skills (Preferred)"))
            for item in match_result.preferred_missing[:4]:
                clean_item = (item[:38] + "..") if len(item) > 40 else item
                lines.append(fmt_row(f"  * {clean_item}"))
    else:
        lines.append(fmt_row("[-] Missing Priority Skills"))
        for item in match_result.missing[:8]:
            clean_item = (item[:38] + "..") if len(item) > 40 else item
            lines.append(fmt_row(f"  * {clean_item}"))

    if not match_result.missing:
        lines.append(fmt_row("  (None missing!)"))

    # 4. ATS Flags & Anti-Pattern Warnings
    ats_flags = []
    if metric_count < total_bullets * 0.5:
        ats_flags.append(f"Low metrics density: only {metric_count}/{total_bullets} quantified")
    if weak_verb_count > 0:
        ats_flags.append(f"{weak_verb_count} bullet(s) open with passive/weak verbs")
    if cliche_matches:
        ats_flags.append(f"{len(cliche_matches)} cliché/overused phrase(s) detected")

    if ats_flags:
        lines.append(border)
        lines.append(fmt_row("[!] ATS Flags & Risk Warnings"))
        for flag in ats_flags[:3]:
            lines.append(fmt_row(f"  ! {flag}"))

    # 5. Actionable High-Impact Quick Wins
    quick_wins = []
    if match_result.required_missing:
        top_missing = match_result.required_missing[0]
        quick_wins.append(f"Add '{top_missing}' — top missing required JD skill")
    if cliche_matches:
        top_cliche = cliche_matches[0]
        quick_wins.append(f"Replace '{top_cliche.phrase}' with: {top_cliche.suggestion.split(',')[0].strip()}")
    elif weak_verb_count > 0:
        quick_wins.append("Strengthen opening verbs with: Architected, Orchestrated")
    if metric_count < total_bullets * 0.7:
        quick_wins.append("Add numbers/KPIs (% improvement, scale, throughput)")

    if quick_wins:
        lines.append(border)
        lines.append(fmt_row("[*] Actionable Quick Wins (Top ROI)"))
        for i, win in enumerate(quick_wins[:3]):
            lines.append(fmt_row(f"  {i+1}. {win}"))

    lines.extend([
        border,
        fmt_row(f"Quality:    {metric_count}/{total_bullets} metrics, {strong_verb_count}/{total_bullets} strong verbs"),
        fmt_row(f"Rewriter:   {rewriter_tier[:34]}"),
        fmt_row(f"Selected:   {selected_exp_count} experiences, {total_bullets} bullets"),
        border
    ])

    return "\n".join(lines)
