from src.models.experience import Experience, TitleConfig, Bullet
from src.models.jd_profile import JDProfile
from src.ranker.experience_ranker import ExperienceRanker
from src.pipeline import Pipeline
from src.models.config import PipelineConfig


def test_actual_employment_gap_handling():
    # User with a 3-year actual employment gap (2019-2022) in their source of truth
    job_recent = Experience(
        id="job_recent",
        company="TechCorp",
        start="2022",
        end="Present",
        importance=9,
        optional=False,
        titles=TitleConfig(default="Senior Software Engineer"),
        bullets=[Bullet(id="b1", text="Built distributed Python services.")]
    )

    job_old = Experience(
        id="job_old",
        company="OldCo",
        start="2016",
        end="2019",
        importance=7,
        optional=False,
        titles=TitleConfig(default="Software Engineer"),
        bullets=[Bullet(id="b2", text="Developed backend APIs with Java.")]
    )

    ranker = ExperienceRanker()
    jd = JDProfile(raw_text="Python and Java engineer", skills=["Python", "Java"], keywords=["python", "java"])

    # Ranking should process both without blocking or throwing errors
    scored = ranker.rank(experiences=[job_recent, job_old], jd_profile=jd)
    assert len(scored) == 2
    assert scored[0].experience.id == "job_recent"
    assert scored[1].experience.id == "job_old"


def test_optional_experience_with_gap_unblocked():
    # Job 1 (recent), Job 2 (optional, low relevance), Job 3 (older)
    j1 = Experience(
        id="j1", company="Co 1", start="2023", end="Present", importance=8, optional=False,
        titles=TitleConfig(default="Dev"), bullets=[Bullet(id="b1", text="Python APIs")]
    )
    j2 = Experience(
        id="j2", company="Co 2", start="2021", end="2022", importance=1, optional=True,
        titles=TitleConfig(default="Dev"), bullets=[Bullet(id="b2", text="Unrelated task")]
    )

    config = PipelineConfig(minimum_similarity=0.3)
    ranker = ExperienceRanker(config=config)
    jd = JDProfile(raw_text="Python API specialist", skills=["Python"], keywords=["python"])

    scored = ranker.rank(experiences=[j1, j2], jd_profile=jd)
    # j2 is optional and low score, so it is safely omitted without blocking
    assert len(scored) == 1
    assert scored[0].experience.id == "j1"
