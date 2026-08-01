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

    def render(self, resume: TailoredResume, template_name: str = "resume.tex.j2") -> str:
        template = self.env.get_template(template_name)
        
        # 1. Contact Info
        contact_data = {
            "name": self.escape_latex(resume.contact_info.name),
            "phone": self.escape_latex(resume.contact_info.phone),
            "email": self.escape_latex(resume.contact_info.email),
            "linkedin": self.escape_latex(resume.contact_info.linkedin),
            "github": self.escape_latex(resume.contact_info.github),
            "location": self.escape_latex(resume.contact_info.location),
        }

        # 2. Education Data
        education_data = []
        for edu in resume.education:
            education_data.append({
                "institution": self.escape_latex(edu.institution),
                "location": self.escape_latex(edu.location),
                "degree": self.escape_latex(edu.degree),
                "dates": self.escape_latex(edu.dates),
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

        # 4. Projects Data
        projects_data = []
        for proj in resume.projects:
            escaped_stack = [self.escape_latex(t) for t in proj.tech_stack]
            projects_data.append({
                "title": self.escape_latex(proj.title),
                "tech_stack_str": ", ".join(escaped_stack),
                "dates": self.escape_latex(proj.dates),
                "bullets": [self.escape_latex(b) for b in proj.bullets]
            })

        # 5. Skills Data
        skills_data = [self.escape_latex(s) for s in resume.selected_skills]

        rendered = template.render(
            contact_info=contact_data,
            education=education_data,
            selected_experiences=experiences_data,
            projects=projects_data,
            selected_skills=skills_data
        )
        return rendered
