import re
import logging

logger = logging.getLogger(__name__)

STRONG_ACTION_VERBS = {
    "designed", "architected", "built", "developed", "implemented", "optimized",
    "reduced", "migrated", "refactored", "automated", "created", "improved",
    "integrated", "analyzed", "deployed", "scaled", "validated", "measured",
    "instrumented", "engineered", "spearheaded", "directed"
}

WEAK_VERBS = {
    "worked", "helped", "assisted", "participated", "supported", "learned",
    "used", "utilized", "responsible", "handled"
}

COMPLEXITY_SIGNALS = {
    "distributed system", "latency", "concurrency", "caching", "database optimization",
    "authentication", "security", "event processing", "search", "real-time",
    "fault tolerance", "deployment", "ci/cd", "observability", "microservices",
    "parallel processing", "high availability", "multi-region", "load balancing",
    "offline synchronization", "performance", "asynchronous"
}

OWNERSHIP_SIGNALS = {
    "owned", "led", "designed", "architected", "implemented", "drove",
    "created", "established", "introduced", "primary"
}


def score_bullet_faang(bullet_text: str) -> float:
    """
    Evaluates a bullet based on FAANG Recruiter standards and returns a multiplier.
    Base multiplier is 1.0. 
    Strong bullets (metrics, ownership, complexity, strong verbs) can get up to ~2.0.
    Weak bullets can drop to ~0.5.
    """
    if not bullet_text or not bullet_text.strip():
        return 1.0

    text_lower = bullet_text.lower().strip()
    multiplier = 1.0
    
    # 1. Metrics / Quantifiable Impact
    # Detects numbers, percentages, or scale indicators (e.g., 50K, 3M, 400GB)
    if re.search(r"\b\d+(?:\.\d+)?%?\b|\b\d+[KMB]\b|\b\d+\+?\s*(users|requests|events|GB|TB)\b", bullet_text):
        multiplier += 0.3
        
    # 2. Action Verbs
    first_word = text_lower.split()[0] if text_lower else ""
    first_word_clean = re.sub(r'[^a-z]', '', first_word)
    
    if first_word_clean in STRONG_ACTION_VERBS:
        multiplier += 0.2
    elif first_word_clean in WEAK_VERBS:
        multiplier -= 0.4
        
    if "responsible for" in text_lower or "worked on" in text_lower:
        multiplier -= 0.3
        
    # 3. Complexity & Technical Depth
    complexity_count = 0
    for signal in COMPLEXITY_SIGNALS:
        if signal in text_lower:
            complexity_count += 1
            
    multiplier += min(0.4, complexity_count * 0.15)
    
    # 4. Ownership
    ownership_count = 0
    for signal in OWNERSHIP_SIGNALS:
        if re.search(rf"\b{signal}\b", text_lower):
            ownership_count += 1
            
    if ownership_count > 0:
        multiplier += 0.15

    # Bound multiplier between 0.5 and 2.5
    return max(0.5, min(2.5, multiplier))
