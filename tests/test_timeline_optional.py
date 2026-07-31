from src.models.experience import Experience, TitleConfig, Bullet
from src.models.jd_profile import JDProfile
from src.ranker.experience_ranker import ExperienceRanker


def test_timeline_optional_tail_drop_only():
    # 3 experiences ordered chronologically (0: newest, 1: middle, 2: oldest)
    e1 = Experience(
        id="job1",
        company="Company A",
        start="2023",
        end="Present",
        importance=10,
        optional=False,
        titles=TitleConfig(default="Senior Dev"),
        bullets=[Bullet(id="b1", text="Python API development")]
    )
    
    e2 = Experience(
        id="job2",
        company="Company B",
        start="2021",
        end="2023",
        importance=1,  # Low score
        optional=True,  # Optional middle job
        titles=TitleConfig(default="Developer"),
        bullets=[Bullet(id="b2", text="Legacy PHP maintenance")]
    )

    e3 = Experience(
        id="job3",
        company="Company C",
        start="2019",
        end="2021",
        importance=9,  # High score, mandatory
        optional=False,
        titles=TitleConfig(default="Junior Dev"),
        bullets=[Bullet(id="b3", text="Database SQL administration")]
    )

    ranker = ExperienceRanker()
    jd = JDProfile(raw_text="Looking for Python API development and SQL administration", skills=["Python", "SQL"], keywords=["python", "sql"])

    scored = ranker.rank(experiences=[e1, e2, e3], jd_profile=jd)
    selected_ids = [s.experience.id for s in scored]

    # Even though Job 2 is optional and has a low score, it CANNOT be dropped
    # because Job 3 is mandatory and dropping Job 2 would create a gap in the timeline!
    assert selected_ids == ["job1", "job2", "job3"]
