from src.ranker.cliche_detector import ClicheDetector


def test_cliche_detector_weak_preambles():
    detector = ClicheDetector()

    bullet = "Responsible for building microservices in Go and managing clusters."
    matches = detector.detect(bullet)
    assert len(matches) >= 1
    assert any(m.category == "weak_preamble" and "responsible for" in m.phrase.lower() for m in matches)
    assert any("spearheaded" in m.suggestion or "owned" in m.suggestion for m in matches)


def test_cliche_detector_buzzwords():
    detector = ClicheDetector()

    bullet = "Self-starter and team player who demonstrated high code quality."
    matches = detector.detect(bullet)
    assert len(matches) >= 2
    categories = [m.category for m in matches]
    assert categories.count("buzzword") >= 2


def test_cliche_detector_vague_verbs():
    detector = ClicheDetector()

    bullet = "Utilized Docker to package applications and changed legacy pipelines."
    matches = detector.detect(bullet)
    assert len(matches) >= 1
    vague_phrases = [m.phrase.lower() for m in matches]
    assert "utilized" in vague_phrases or "changed" in vague_phrases


def test_cliche_detector_clean_bullet():
    detector = ClicheDetector()

    bullet = "Architected a multi-region Kubernetes platform across AWS EKS, sustaining 99.99% availability under 250K peak RPS."
    matches = detector.detect(bullet)
    assert len(matches) == 0
    assert detector.score_bullet_penalty(bullet) == 0.0


def test_cliche_penalty_calculation():
    detector = ClicheDetector()

    bullet = "Responsible for duties included being a team player who used Python."
    penalty = detector.score_bullet_penalty(bullet)
    assert penalty > 0.3
