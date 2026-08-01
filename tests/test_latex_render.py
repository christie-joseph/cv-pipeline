from pathlib import Path
from src.models.experience import Experience, TitleConfig, Bullet
from src.models.resume import TailoredResume, SelectedExperience, SelectedBullet, ContactInfo, EducationItem, ProjectItem
from src.renderer.latex_renderer import LatexRenderer

project_root = Path(__file__).resolve().parent.parent


def test_latex_renderer():
    template_dir = str(project_root / "templates")
    renderer = LatexRenderer(template_dir=template_dir)

    exp = Experience(
        id="amazon",
        company="Amazon & Co.",
        start="2022",
        end="Present",
        importance=9,
        titles=TitleConfig(default="Software Engineer"),
        bullets=[Bullet(id="b1", text="Built 50% faster API with Java & C++")]
    )

    resume = TailoredResume(
        contact_info=ContactInfo(name="Jake Ryan", email="jake@su.edu", phone="123-456-7890"),
        education=[EducationItem(institution="University of Birmingham", location="UK", degree="MSc Computer Science", dates="2022")],
        projects=[ProjectItem(id="p1", title="Gitlytics", tech_stack=["Python", "React"], dates="2020", bullets=["Built dashboard."])],
        selected_experiences=[
            SelectedExperience(
                experience=exp,
                selected_title="Backend Software Engineer",
                selected_bullets=[
                    SelectedBullet(bullet=exp.bullets[0], rewritten_text="Built 50% faster API with Java & C++")
                ]
            )
        ],
        selected_skills=["Java", "C++", "AWS"]
    )

    latex_str = renderer.render(resume)
    assert "\\begin{document}" in latex_str
    assert "Jake Ryan" in latex_str
    assert "\\resumeSubheading" in latex_str
    assert "Backend Software Engineer" in latex_str
    assert "\\&" in latex_str  # Escaped ampersand
