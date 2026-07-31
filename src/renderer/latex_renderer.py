import os
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
        """Escapes LaTeX special characters while avoiding double-escaping."""
        if not text:
            return ""
        
        result = text
        result = re.sub(r'(?<!\\)&', r'\&', result)
        result = re.sub(r'(?<!\\)%', r'\%', result)
        result = re.sub(r'(?<!\\)\$', r'\$', result)
        result = re.sub(r'(?<!\\)#', r'\#', result)
        result = re.sub(r'(?<!\\)_', r'\_', result)
        result = re.sub(r'(?<!\\)\{', r'\{', result)
        result = re.sub(r'(?<!\\)\}', r'\}', result)
        return result

    def render(self, resume: TailoredResume, template_name: str = "resume.tex.j2") -> str:
        template = self.env.get_template(template_name)
        
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

        skills_data = [self.escape_latex(s) for s in resume.selected_skills]

        rendered = template.render(
            selected_experiences=experiences_data,
            selected_skills=skills_data
        )
        return rendered
