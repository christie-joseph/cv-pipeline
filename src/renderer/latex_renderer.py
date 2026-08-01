import re
import jinja2
from pathlib import Path
from typing import Optional
from ..models.resume import TailoredResume


class LatexRenderer:
    def __init__(self, template_dir: Optional[str] = None):
        if not template_dir:
            project_root = Path(__file__).resolve().parent.parent.parent
            template_dir = str(project_root / "templates")
            
        self.template_dir = template_dir
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

    def escape_latex(self, text: str) -> str:
        """Escapes LaTeX special characters in strict deterministic order."""
        if not text:
            return ""
        
        # 1. First escape backslashes to prevent double-escaping downstream
        result = text.replace("\\", r"\textbackslash{}")
        
        # 2. Escape special characters
        replacements = [
            ("&", r"\&"),
            ("%", r"\%"),
            ("$", r"\$"),
            ("#", r"\#"),
            ("_", r"\_"),
            ("{", r"\{"),
            ("}", r"\}"),
            ("~", r"\textasciitilde{}"),
            ("^", r"\textasciicircum{}"),
        ]
        
        for char, sub in replacements:
            pattern = r"(?<!\\)" + re.escape(char)
            result = re.sub(pattern, sub, result)
            
        return result

    def _extract_grad_year(self, dates_str: str) -> str:
        """Extracts graduation year from dates string (e.g. 'Sept 2021 -- Sept 2022' -> '2022')."""
        if not dates_str:
            return ""
        years = re.findall(r"\b(20\d{2}|19\d{2})\b", dates_str)
        if years:
            return years[-1]
        return dates_str

    def render(self, resume: TailoredResume, template_name: str = "resume.tex.j2") -> str:
        template = self.env.get_template(template_name)
        
        # 1. Contact Info & Line Assembly (Name and Email required, others optional)
        contact_parts = []
        if resume.contact_info.email:
            esc_email = self.escape_latex(resume.contact_info.email)
            contact_parts.append(f"\\href{{mailto:{esc_email}}}{{\\underline{{{esc_email}}}}}")
        if resume.contact_info.phone:
            contact_parts.append(self.escape_latex(resume.contact_info.phone))
        if resume.contact_info.linkedin:
            esc_li = self.escape_latex(resume.contact_info.linkedin)
            contact_parts.append(f"\\href{{https://{esc_li}}}{{\\underline{{{esc_li}}}}}")
        if resume.contact_info.github:
            esc_gh = self.escape_latex(resume.contact_info.github)
            contact_parts.append(f"\\href{{https://{esc_gh}}}{{\\underline{{{esc_gh}}}}}")
            
        contact_data = {
            "name": self.escape_latex(resume.contact_info.name),
            "contact_line": " $|$ ".join(contact_parts)
        }

        # Target Role
        target_role = self.escape_latex(resume.metadata.get("target_role", ""))

        # 2. Education Data (Graduation Year only)
        education_data = []
        for edu in resume.education:
            education_data.append({
                "institution": self.escape_latex(edu.institution),
                "location": self.escape_latex(edu.location),
                "degree": self.escape_latex(edu.degree),
                "dates": self.escape_latex(self._extract_grad_year(edu.dates)),
            })

        # 3. Selected Experiences Data
        experiences_data = []
        for sel_exp in resume.selected_experiences:
            exp = sel_exp.experience
            
            escaped_exp = {
                "company": self.escape_latex(exp.company),
                "start": self.escape_latex(exp.start),
                "end": self.escape_latex(exp.end),
            }
            
            bullets_data = []
            for sel_bullet in sel_exp.selected_bullets:
                text_to_escape = sel_bullet.rewritten_text or sel_bullet.bullet.text
                bullets_data.append({"rewritten_text": self.escape_latex(text_to_escape)})
            
            experiences_data.append({
                "experience": escaped_exp,
                "selected_title": self.escape_latex(sel_exp.selected_title),
                "selected_bullets": bullets_data
            })

        # 4. Projects Data (No dates)
        projects_data = []
        for proj in resume.projects:
            escaped_stack = [self.escape_latex(t) for t in proj.tech_stack]
            projects_data.append({
                "title": self.escape_latex(proj.title),
                "tech_stack_str": ", ".join(escaped_stack),
                "bullets": [self.escape_latex(b) for b in proj.bullets]
            })

        # 5. Skills Data
        skills_data = [self.escape_latex(s) for s in resume.selected_skills]

        rendered = template.render(
            contact_info=contact_data,
            target_role=target_role,
            education=education_data,
            selected_experiences=experiences_data,
            projects=projects_data,
            selected_skills=skills_data
        )
        return rendered
