from typing import Optional
from ..models.resume import TailoredResume


class MarkdownExporter:
    """
    Renders a TailoredResume instance into clean, beautifully formatted Markdown.
    Optimized for pasting into text-only ATS application portals (Greenhouse, Lever, Workday)
    or sharing as a standalone plaintext/markdown document.
    """

    def export(self, resume: TailoredResume) -> str:
        lines = []

        # 1. Contact Header
        name = resume.contact_info.name or "Candidate"
        lines.append(f"# {name}")
        contact_items = []
        if resume.contact_info.email:
            contact_items.append(resume.contact_info.email)
        if resume.contact_info.phone:
            contact_items.append(resume.contact_info.phone)
        if resume.contact_info.location:
            contact_items.append(resume.contact_info.location)
        if resume.contact_info.linkedin:
            contact_items.append(resume.contact_info.linkedin)
        if resume.contact_info.github:
            contact_items.append(resume.contact_info.github)

        if contact_items:
            lines.append(" | ".join(contact_items))
        lines.append("")

        # 2. Selected Professional Experience
        lines.append("## Professional Experience")
        lines.append("")

        for sel_exp in resume.selected_experiences:
            exp = sel_exp.experience
            title = sel_exp.selected_title or exp.titles.default
            company = exp.company
            dates = f"{exp.start} — {exp.end}"

            lines.append(f"### {title} | **{company}**")
            lines.append(f"*{dates}*")
            lines.append("")

            for b in sel_exp.selected_bullets:
                b_text = b.rewritten_text or b.bullet.text
                lines.append(f"- {b_text}")
            lines.append("")

        # 3. Selected Projects
        if resume.projects:
            lines.append("## Key Projects")
            lines.append("")
            for proj in resume.projects:
                tech_str = f" ({', '.join(proj.tech_stack)})" if proj.tech_stack else ""
                lines.append(f"### {proj.title}{tech_str}")
                for b_text in proj.bullets:
                    lines.append(f"- {b_text}")
                lines.append("")

        # 4. Education
        if resume.education:
            lines.append("## Education")
            lines.append("")
            for edu in resume.education:
                degree_part = f"{edu.degree} in {edu.major}" if edu.major else edu.degree
                inst_part = f"**{edu.institution}**"
                date_part = f" ({edu.dates})" if edu.dates else ""
                lines.append(f"- {degree_part} — {inst_part}{date_part}")
            lines.append("")

        # 5. Technical Skills
        if resume.selected_skills:
            lines.append("## Technical Skills")
            lines.append("")
            lines.append(", ".join(dict.fromkeys(resume.selected_skills)))
            lines.append("")

        return "\n".join(lines).strip() + "\n"
