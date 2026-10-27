import re
import jinja2
from pathlib import Path
from typing import Optional, List, Dict
from ..models.resume import TailoredResume
from ..models.experience import SkillTaxonomy

_LATEX_SPECIAL_MAP = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_LATEX_PATTERN = re.compile("|".join(re.escape(k) for k in _LATEX_SPECIAL_MAP.keys()))


class LatexRenderer:
    def __init__(self, template_dir: Optional[str] = None):
        project_root = Path(__file__).resolve().parent.parent.parent
        if not template_dir:
            template_dir = str(project_root / "templates")
            
        self.template_dir = template_dir
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.taxonomy = SkillTaxonomy.load_from_yaml(str(project_root / "data" / "skills.yaml"))
        g_path = project_root / "data" / "global_skills.yaml"
        self.global_taxonomy = SkillTaxonomy.load_from_yaml(str(g_path)) if g_path.exists() else None

    def escape_latex(self, text: str) -> str:
        """Escapes LaTeX special characters in a single pass to prevent double-escaping."""
        if not text:
            return ""
        return _LATEX_PATTERN.sub(lambda m: _LATEX_SPECIAL_MAP[m.group(0)], text)

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
        
        # 1. Contact Info & Line Assembly (URLs should NOT be escaped in href target)
        contact_parts = []
        if resume.contact_info.email:
            esc_email = self.escape_latex(resume.contact_info.email)
            contact_parts.append(f"\\href{{mailto:{resume.contact_info.email}}}{{\\underline{{{esc_email}}}}}")
        if resume.contact_info.phone:
            contact_parts.append(self.escape_latex(resume.contact_info.phone))
        if resume.contact_info.linkedin:
            li_clean = re.sub(r"^https?://", "", resume.contact_info.linkedin)
            esc_li = self.escape_latex(li_clean)
            contact_parts.append(f"\\href{{https://{li_clean}}}{{\\underline{{{esc_li}}}}}")
        if resume.contact_info.github:
            gh_clean = re.sub(r"^https?://", "", resume.contact_info.github)
            esc_gh = self.escape_latex(gh_clean)
            contact_parts.append(f"\\href{{https://{gh_clean}}}{{\\underline{{{esc_gh}}}}}")
            
        contact_data = {
            "name": self.escape_latex(resume.contact_info.name),
            "contact_line": " $|$ ".join(contact_parts)
        }

        # Target Role
        target_role = self.escape_latex(resume.metadata.get("target_role", ""))

        # 2. Education Data (Graduation Year only)
        education_data = []
        for edu in resume.education:
            degree_str = self.escape_latex(edu.degree)
            major_str = self.escape_latex(edu.major)
            full_degree = f"{degree_str} in {major_str}" if major_str else degree_str

            education_data.append({
                "institution": self.escape_latex(edu.institution),
                "location": self.escape_latex(edu.location),
                "degree": degree_str,
                "major": major_str,
                "full_degree": full_degree,
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

        # 5. Categorize Skills dynamically from taxonomy & selected_skills
        # Map skill display to its canonical category
        skill_to_cat = {}
        all_skills = []
        if self.taxonomy:
            all_skills.extend(self.taxonomy.skills)
        if self.global_taxonomy:
            all_skills.extend(self.global_taxonomy.skills)

        for s in all_skills:
            cat = s.category or "Technologies"
            # Normalize naming: 'Tools' -> 'Technologies', 'Cloud Services' -> 'Cloud'
            if cat.lower() in ["tools", "frameworks & libraries", "frameworks"]:
                cat = "Frameworks"
            elif cat.lower() in ["cloud", "cloud services"]:
                cat = "Cloud"
            elif cat.lower() in ["databases"]:
                cat = "Databases"
            elif cat.lower() in ["languages"]:
                cat = "Languages"
            skill_to_cat[s.display.lower()] = (s.display, cat)
            for a in s.aliases:
                skill_to_cat[a.lower()] = (s.display, cat)

        # Standard canonical category order
        desired_categories = ["Languages", "Frameworks", "Databases", "Cloud", "Technologies"]
        category_skills = {c: [] for c in desired_categories}

        # First, populate from resume.selected_skills
        selected_set = set()
        for sk in resume.selected_skills:
            sk_clean = sk.strip()
            lookup = skill_to_cat.get(sk_clean.lower())
            if lookup:
                disp, cat = lookup
                if cat not in category_skills:
                    cat = "Technologies"
                if disp not in category_skills[cat]:
                    category_skills[cat].append(disp)
                    selected_set.add(disp.lower())
            else:
                category_skills["Technologies"].append(sk_clean)
                selected_set.add(sk_clean.lower())

        # If a category is empty, pull relevant defaults from self.taxonomy or global_taxonomy
        for s in all_skills:
            cat = s.category or "Technologies"
            if cat.lower() in ["tools", "frameworks", "frameworks & libraries"]:
                cat = "Frameworks"
            elif cat.lower() in ["cloud", "cloud services"]:
                cat = "Cloud"
            elif cat.lower() in ["databases"]:
                cat = "Databases"
            elif cat.lower() in ["languages"]:
                cat = "Languages"
            else:
                cat = "Technologies"

            if cat in category_skills and len(category_skills[cat]) < 2:
                if s.display.lower() not in selected_set:
                    category_skills[cat].append(s.display)
                    selected_set.add(s.display.lower())

        # Fallback guarantee for any still-empty desired category
        fallbacks = {
            "Languages": ["Python", "Java"],
            "Frameworks": ["React", "FastAPI"],
            "Databases": ["PostgreSQL", "Redis"],
            "Cloud": ["AWS", "Docker"],
            "Technologies": ["Git", "CI/CD"]
        }
        for cat in desired_categories:
            if not category_skills[cat]:
                category_skills[cat] = fallbacks.get(cat, ["General"])

        skill_categories_data = []
        for cat in desired_categories:
            if category_skills[cat]:
                esc_skills = [self.escape_latex(x) for x in category_skills[cat]]
                skill_categories_data.append({
                    "name": self.escape_latex(cat),
                    "skills_str": ", ".join(esc_skills)
                })


        rendered = template.render(
            contact_info=contact_data,
            target_role=target_role,
            education=education_data,
            selected_experiences=experiences_data,
            projects=projects_data,
            skill_categories=skill_categories_data
        )
        return rendered
