from src.models.experience import Experience, TitleConfig, Bullet
from src.models.resume import TailoredResume, SelectedExperience, SelectedBullet
from src.renderer.latex_renderer import LatexRenderer


def test_latex_renderer():
    renderer = LatexRenderer(template_dir="templates")

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
    assert "Backend Software Engineer" in latex_str
    assert "\\&" in latex_str  # Escaped ampersand
