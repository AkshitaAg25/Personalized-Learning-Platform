
from datetime import datetime, timezone


# ── Topic alias normalisation ─────────────────────────────────────────────────
# Maps any variant → canonical label.  Add entries as subjects grow.

_ALIASES: dict[str, str] = {
    # OOP variants
    "oop":                          "OOP",
    "object oriented programming":  "OOP",
    "object-oriented":              "OOP",
    "object oriented":              "OOP",
    # Data Structures
    "data structure":               "Data Structures",
    "data structures":              "Data Structures",
    # Algorithms
    "algorithm":                    "Algorithms",
    "algorithms":                   "Algorithms",
    # CS fundamentals
    "programming basics":           "Programming Basics",
    "programming fundamental":      "Programming Basics",
    # Machine Learning
    "ml":                           "Machine Learning",
    "machine learning":             "Machine Learning",
    "deep learning":                "Deep Learning",
    # Math
    "calc":                         "Calculus",
    "calculus":                     "Calculus",
    "linear algebra":               "Linear Algebra",
    "prob":                         "Probability",
    "probability":                  "Probability",
    "stats":                        "Statistics",
    "statistics":                   "Statistics",
    "combinatorics":                "Combinatorics",
    "number theory":                "Number Theory",
    "graph theory":                 "Graph Theory",
    # Science
    "classical mechanics":          "Classical Mechanics",
    "mechanics":                    "Classical Mechanics",
    "thermodynamics":               "Thermodynamics",
    "quantum mechanics":            "Quantum Mechanics",
    "quantum":                      "Quantum Mechanics",
    "genetics":                     "Genetics",
    "cell biology":                 "Cell Biology",
    "atomic theory":                "Atomic Theory",
    "electromagnetism":             "Electromagnetism",
    "evolution":                    "Evolution",
}

# Keyword → canonical topic (used when no focus hint matches)
_KEYWORD_MAP: dict[str, str] = {
    # OOP
    "class":        "OOP",
    "object":       "OOP",
    "inheritance":  "OOP",
    "polymorphism": "OOP",
    "encapsulation":"OOP",
    "constructor":  "OOP",
    "decorator":    "OOP",
    "__init__":     "OOP",
    # Data Structures
    "array":        "Data Structures",
    "linked list":  "Data Structures",
    "stack":        "Data Structures",
    "queue":        "Data Structures",
    "tree":         "Data Structures",
    "heap":         "Data Structures",
    "hash":         "Data Structures",
    # Algorithms
    "sort":         "Algorithms",
    "search":       "Algorithms",
    "complexity":   "Algorithms",
    "big-o":        "Algorithms",
    "big o":        "Algorithms",
    "binary search":"Algorithms",
    "recursion":    "Recursion",
    "recursive":    "Recursion",
    # Databases
    "sql":          "Databases",
    "database":     "Databases",
    "query":        "Databases",
    "table":        "Databases",
    "join":         "Databases",
    # Networking
    "http":         "Networking",
    "tcp":          "Networking",
    "ip ":          "Networking",
    "dns":          "Networking",
    "protocol":     "Networking",
    # ML / AI
    "neural":       "Machine Learning",
    "machine learn":"Machine Learning",
    "gradient":     "Machine Learning",
    "training":     "Machine Learning",
    "model":        "Machine Learning",
    # Math – Calculus
    "derivative":   "Calculus",
    "integral":     "Calculus",
    "limit":        "Calculus",
    "differential": "Calculus",
    # Math – Linear Algebra
    "matrix":       "Linear Algebra",
    "vector":       "Linear Algebra",
    "eigenvalue":   "Linear Algebra",
    # Math – Probability/Stats
    "probability":  "Probability",
    "random":       "Probability",
    "distribution": "Statistics",
    "mean":         "Statistics",
    "variance":     "Statistics",
    # Math – Combinatorics
    "factorial":    "Combinatorics",
    "permutation":  "Combinatorics",
    "combination":  "Combinatorics",
    # Math – Number Theory
    "prime":        "Number Theory",
    "modulo":       "Number Theory",
    "divisib":      "Number Theory",
    # Science
    "force":        "Classical Mechanics",
    "velocity":     "Classical Mechanics",
    "momentum":     "Classical Mechanics",
    "newton":       "Classical Mechanics",
    "energy":       "Thermodynamics",
    "entropy":      "Thermodynamics",
    "heat":         "Thermodynamics",
    "atom":         "Atomic Theory",
    "electron":     "Atomic Theory",
    "quantum":      "Quantum Mechanics",
    "photon":       "Quantum Mechanics",
    "gene":         "Genetics",
    "dna":          "Genetics",
    "cell":         "Cell Biology",
    "membrane":     "Cell Biology",
    "electric":     "Electromagnetism",
    "magnetic":     "Electromagnetism",
    "evolution":    "Evolution",
    "natural select":"Evolution",
}


def _canonical(label: str) -> str:
    """Return the canonical topic label for any alias/variant."""
    return _ALIASES.get(label.lower().strip(), label.strip().title())


def _tag_question(question_text: str, focus: str, subject: str) -> str:

    q       = question_text.lower()
    focus_n = focus.lower().strip() if focus else ""

    # 1. Focus hint — if the question is clearly about the focus area
    if focus_n and focus_n in q:
        return _canonical(focus)

    # 2. Keyword scan
    for keyword, topic in _KEYWORD_MAP.items():
        if keyword in q:
            return topic

    # 3. Fallback
    if focus:
        return _canonical(focus)
    return _canonical(subject)


def _classify_level(percentage: float) -> str:
    if percentage >= 80:
        return "advanced"
    elif percentage >= 50:
        return "intermediate"
    else:
        return "beginner"


# ── Public API ────────────────────────────────────────────────────────────────

def evaluate_quiz(form_data: dict) -> dict:
    
    subject  = form_data.get("subject", "General")
    focus    = form_data.get("focus", "")
    mastered = form_data.get("mastered", "")
    total    = int(form_data.get("total", 5))

    topic_scores: dict[str, dict] = {}
    score = 0

    for i in range(total):
        user_ans    = form_data.get(f"q{i}", "").strip()
        correct_ans = form_data.get(f"correct{i}", "").strip()
        q_text      = form_data.get(f"question{i}", f"Question {i+1}")

        is_correct = user_ans.lower() == correct_ans.lower()
        if is_correct:
            score += 1

        topic = _tag_question(q_text, focus, subject)

        if topic not in topic_scores:
            topic_scores[topic] = {"correct": 0, "total": 0, "questions": []}

        topic_scores[topic]["total"]   += 1
        topic_scores[topic]["correct"] += int(is_correct)
        topic_scores[topic]["questions"].append({
            "question":    q_text,
            "user_ans":    user_ans,
            "correct_ans": correct_ans,
            "is_correct":  is_correct,
        })

    for topic, data in topic_scores.items():
        data["accuracy"] = (
            round(data["correct"] / data["total"] * 100, 1)
            if data["total"] > 0 else 0.0
        )

    percentage = round(score / total * 100, 1) if total > 0 else 0.0
    level      = _classify_level(percentage)

    weak_areas   = [t for t, d in topic_scores.items() if d["accuracy"] <  50]
    strong_areas = [t for t, d in topic_scores.items() if d["accuracy"] >= 80]

    return {
        "subject":      subject,
        "focus":        focus,
        "mastered":     mastered,
        "score":        score,
        "total":        total,
        "percentage":   percentage,
        "level":        level,
        "topic_scores": topic_scores,
        "weak_areas":   weak_areas,
        "strong_areas": strong_areas,
        "timestamp":    datetime.now(timezone.utc).isoformat(),
    }
