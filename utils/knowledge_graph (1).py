
from __future__ import annotations
import json
import os
import re


def _word_match(a: str, b: str) -> bool:
    """True if a and b are the same topic (whole-word, not substring accident)."""
    a_n = a.lower().strip()
    b_n = b.lower().strip()
    if a_n == b_n:
        return True
    if re.search(r'\b' + re.escape(a_n) + r'\b', b_n):
        return True
    if re.search(r'\b' + re.escape(b_n) + r'\b', a_n):
        return True
    return False

try:
    from google import genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


# ── Gemini client ─────────────────────────────────────────────────────────────

def _get_client():
    api_key = os.environ.get("GEMINI_API_KEY", "google ai studio api key here")
    if not _GENAI_AVAILABLE:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


# ── Prerequisite inference via Gemini ─────────────────────────────────────────

def _infer_prerequisites_gemini(topics: list[str], subject: str, mastered: str) -> list[dict]:
    """
    Ask Gemini: given these exact topics in this subject, which ones are
    prerequisites of which?  Returns list of {source, target, type} edges.
    Falls back to an empty edge list if Gemini is unavailable.
    """
    client = _get_client()
    if not client or len(topics) < 2:
        return []

    prompt = f"""
You are a curriculum designer. A student is learning {subject}.
They have already mastered: {mastered or "nothing yet"}.

The student was tested on these specific topics: {json.dumps(topics)}

Return ONLY a JSON array of prerequisite/related edges between those topics.
Each edge must be: {{"source": "<topic>", "target": "<topic>", "type": "prerequisite"|"related"}}

Rules:
- Only use topics from the list above, spelled exactly the same way
- "prerequisite" means you must understand source before target
- "related" means the topics reinforce each other but neither is strictly required first
- Do not add any topic not in the list
- Return only the JSON array, no explanation, no markdown fences

Example output for topics ["Arrays", "Recursion", "Sorting"]:
[
  {{"source": "Arrays", "target": "Sorting", "type": "prerequisite"}},
  {{"source": "Recursion", "target": "Sorting", "type": "related"}}
]
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw = response.text.replace("```json", "").replace("```", "").strip()
        edges = json.loads(raw)
        # Validate: only keep edges whose source+target are in our topic list
        topic_set = set(topics)
        return [
            e for e in edges
            if isinstance(e, dict)
            and e.get("source") in topic_set
            and e.get("target") in topic_set
            and e.get("type") in ("prerequisite", "related")
        ]
    except Exception:
        return []


# ── Tier computation from graph depth ─────────────────────────────────────────

def _compute_tiers(topics: list[str], edges: list[dict]) -> dict[str, int]:
    """
    Assign tier 1/2/3 to each topic based on its depth in the prerequisite DAG.
    Nodes with no prerequisites = tier 1 (foundation).
    Nodes with depth 1 = tier 2.  Depth 2+ = tier 3.
    """
    # Build adjacency: who does each node depend on?
    prereqs: dict[str, set] = {t: set() for t in topics}
    for e in edges:
        if e["type"] == "prerequisite":
            prereqs[e["target"]].add(e["source"])

    # Topological depth via BFS from roots
    depth: dict[str, int] = {}

    def get_depth(topic: str, visiting: set) -> int:
        if topic in depth:
            return depth[topic]
        if topic in visiting:
            return 0  # cycle guard
        visiting.add(topic)
        if not prereqs[topic]:
            depth[topic] = 0
        else:
            depth[topic] = 1 + max(get_depth(p, visiting) for p in prereqs[topic])
        visiting.discard(topic)
        return depth[topic]

    for t in topics:
        get_depth(t, set())

    # Map depth → tier
    tiers = {}
    for t, d in depth.items():
        if d == 0:
            tiers[t] = 1
        elif d == 1:
            tiers[t] = 2
        else:
            tiers[t] = 3

    return tiers


# ── Status assignment ─────────────────────────────────────────────────────────

def _assign_status(
    topic: str,
    accuracy: float | None,
    focus: str,
    mastered_declared: list[str],
    weak_areas: list[str],
    strong_areas: list[str],
) -> str:
    topic_n = topic.lower().strip()

    # User declared they already know this
    if any(_word_match(topic, m) for m in mastered_declared if m):
        return "mastered"

    # From quiz results (accuracy beats everything else)
    if accuracy is not None:
        if accuracy >= 80:
            return "mastered"
        elif accuracy < 50:
            return "weak"

    # User's stated focus area
    if focus and _word_match(topic, focus):
        return "focus"

    # Cross-check weak/strong lists
    if any(_word_match(topic, w) for w in weak_areas if w):
        return "weak"
    if any(_word_match(topic, s) for s in strong_areas if s):
        return "mastered"

    return "untouched"


# ── Level-aware entry point selection ─────────────────────────────────────────

def _select_entry_points(nodes: list[dict], level: str) -> list[str]:
    """
    Pick where the learner should start based on their quiz level:
      beginner     → tier-1 weak/untouched nodes first
      intermediate → tier-2 weak/focus nodes first
      advanced     → tier-3 weak/focus nodes first, or tier-2 if none
    """
    def candidates(tier: int, statuses: list[str]) -> list[str]:
        return [n["id"] for n in nodes if n["tier"] == tier and n["status"] in statuses]

    if level == "beginner":
        pts = candidates(1, ["weak", "untouched", "focus"])
        if not pts:
            pts = candidates(2, ["weak", "untouched", "focus"])

    elif level == "intermediate":
        pts = candidates(2, ["weak", "focus", "untouched"])
        if not pts:
            pts = candidates(1, ["weak", "untouched"])

    else:  # advanced
        pts = candidates(3, ["weak", "focus", "untouched"])
        if not pts:
            pts = candidates(2, ["weak", "focus", "untouched"])

    return pts


# ── Public API ────────────────────────────────────────────────────────────────

def build_knowledge_graph(evaluation_result: dict) -> dict:
    """
    Builds a knowledge graph entirely from the quiz's actual topics.

    Steps:
      1. Extract real tested topics from evaluation_result["topic_scores"]
      2. Infer prerequisite edges via Gemini (falls back to empty if unavailable)
      3. Compute node tiers from graph depth
      4. Assign statuses from quiz accuracy + declared mastered/focus
      5. Select level-appropriate entry points
    """
    subject      = evaluation_result.get("subject", "General")
    focus        = evaluation_result.get("focus", "")
    mastered_raw = evaluation_result.get("mastered", "")
    level        = evaluation_result.get("level", "beginner")
    topic_scores = evaluation_result.get("topic_scores", {})
    weak_areas   = evaluation_result.get("weak_areas", [])
    strong_areas = evaluation_result.get("strong_areas", [])

    mastered_declared = [m.strip() for m in mastered_raw.split(",") if m.strip()]

    # ── 1. Real topics from the quiz ─────────────────────────────────────────
    tested_topics = list(topic_scores.keys())

    # Also surface the user's declared mastered topics as nodes (even if not
    # in the quiz) so the graph shows what they already know
    for m in mastered_declared:
        if m and m not in tested_topics:
            tested_topics.append(m)

    if not tested_topics:
        tested_topics = [subject]

    # ── 2. Gemini-inferred edges ──────────────────────────────────────────────
    edges = _infer_prerequisites_gemini(tested_topics, subject, mastered_raw)

    # ── 3. Tier from graph depth ──────────────────────────────────────────────
    tiers = _compute_tiers(tested_topics, edges)

    # ── 4. Build nodes with status + accuracy ────────────────────────────────
    nodes = []
    for topic in tested_topics:
        score_data = topic_scores.get(topic)
        accuracy   = score_data["accuracy"] if score_data else None

        # Declared mastered topics not in the quiz get 100% accuracy shown
        if accuracy is None and topic in mastered_declared:
            accuracy = 100.0

        status = _assign_status(
            topic, accuracy, focus,
            mastered_declared, weak_areas, strong_areas
        )

        nodes.append({
            "id":       topic,           # use topic name directly as id
            "label":    topic,
            "subject":  subject,
            "tier":     tiers.get(topic, 1),
            "status":   status,
            "accuracy": accuracy,
        })

    # ── 5. Level-aware entry points ───────────────────────────────────────────
    entry_points = _select_entry_points(nodes, level)

    # Fallback: if nothing selected, pick all weak nodes
    if not entry_points:
        entry_points = [n["id"] for n in nodes if n["status"] == "weak"]
    if not entry_points and nodes:
        entry_points = [nodes[0]["id"]]

    return {
        "subject":      subject,
        "nodes":        nodes,
        "edges":        edges,
        "entry_points": entry_points,
        "level":        level,
    }
