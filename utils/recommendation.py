
from __future__ import annotations
import json, os

try:
    from google import genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


def _client():
    key = os.environ.get("GEMINI_API_KEY", "")
    if not _GENAI_AVAILABLE:
        return None
    try:
        return genai.Client(api_key=key)
    except Exception:
        return None


def _call_gemini(prompt: str) -> str:
    c = _client()
    if not c:
        return "{}"
    try:
        r = c.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return r.text.replace("```json","").replace("```","").strip()
    except Exception:
        return "{}"


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Generate the full learning path via Gemini
# ─────────────────────────────────────────────────────────────────────────────

def _generate_path(eval_result: dict, kg_nodes: list[dict]) -> list[dict]:
    """
    Ask Gemini to order the quiz topics into a personalised learning path.
    Returns list of path step dicts.
    """
    subject      = eval_result.get("subject","")
    level        = eval_result.get("level","beginner")
    focus        = eval_result.get("focus","")
    mastered_raw = eval_result.get("mastered","")
    score        = eval_result.get("score",0)
    total        = eval_result.get("total",5)
    topic_scores = eval_result.get("topic_scores",{})

    # Build a compact topic summary for Gemini
    topics_info = []
    for n in kg_nodes:
        ts = topic_scores.get(n["id"], {})
        acc = ts.get("accuracy") if ts else n.get("accuracy")
        topics_info.append({
            "topic":    n["id"],
            "status":   n["status"],
            "tier":     n["tier"],
            "accuracy": acc,
        })

    prompt = f"""
You are an expert learning coach. A student just completed a {subject} quiz.

Student profile:
- Knowledge level: {level}
- Quiz score: {score}/{total}
- Focus area: {focus or "general"}
- Already mastered: {mastered_raw or "none stated"}

Topics tested and their results:
{json.dumps(topics_info, indent=2)}

Create a personalised learning path of up to 6 steps. Each step must address one of the topics above.
Prioritise:
1. Weak topics (accuracy < 50%) — action: "review"
2. Focus topic if weak or untested — action: "practice"  
3. Untouched important topics for this level — action: "learn"
4. Strong topics only for advanced students — action: "challenge"

For a {level} student:
- beginner: start with foundational topics, build up gradually
- intermediate: focus on gaps and consolidation
- advanced: push toward harder applications and edge cases

Return ONLY a JSON array (no markdown) of steps like:
[
  {{
    "order": 1,
    "topic": "exact topic name from the list",
    "action": "review|learn|practice|challenge",
    "reason": "One specific sentence explaining why this step matters for THIS student right now.",
    "what_to_do": "Two or three concrete sentences telling the student exactly what to do in this step."
  }}
]
"""
    raw = _call_gemini(prompt)
    try:
        steps = json.loads(raw)
        if not isinstance(steps, list):
            return []
        # Validate and enrich steps with node metadata
        node_map = {n["id"]: n for n in kg_nodes}
        result = []
        for s in steps:
            if not isinstance(s, dict) or not s.get("topic"):
                continue
            node = node_map.get(s["topic"], {})
            result.append({
                "order":    s.get("order", len(result)+1),
                "node_id":  s["topic"],
                "label":    s["topic"],
                "action":   s.get("action","learn"),
                "reason":   s.get("reason",""),
                "what_to_do": s.get("what_to_do",""),
                "status":   node.get("status","untouched"),
                "tier":     node.get("tier",1),
                "accuracy": node.get("accuracy"),
            })
        return result
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Generate real resources for top path topics
# ─────────────────────────────────────────────────────────────────────────────

def _generate_resources(topics: list[str], subject: str, level: str) -> dict[str, list[dict]]:
    if not topics:
        return {}

    prompt = f"""
A {level}-level student studying {subject} needs learning resources for these topics:
{json.dumps(topics)}

For each topic provide exactly 3 real resources. Use only well-known platforms with real URLs:
Khan Academy, MIT OpenCourseWare, Coursera, edX, freeCodeCamp, MDN Web Docs, W3Schools,
Brilliant.org, GeeksforGeeks, YouTube (specific channels like 3Blue1Brown, CS50, Crash Course),
Codecademy, LeetCode, HackerRank, or similar authoritative sources.

Match difficulty to {level} level.

Return ONLY a JSON object (no markdown):
{{
  "Topic Name": [
    {{
      "title": "Specific resource title",
      "type": "video|article|exercise|course",
      "url": "https://actual-real-url.com/specific-path",
      "platform": "Khan Academy",
      "description": "One sentence on what this resource covers and why it helps."
    }}
  ]
}}
"""
    raw = _call_gemini(prompt)
    try:
        resources = json.loads(raw)
        validated = {}
        for topic, items in resources.items():
            if isinstance(items, list):
                validated[topic] = [
                    r for r in items
                    if isinstance(r,dict) and r.get("title") and r.get("url")
                ][:3]
        return validated
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def build_recommendation_path(evaluation_result: dict, knowledge_graph: dict) -> dict:
    level    = evaluation_result.get("level","beginner")
    subject  = evaluation_result.get("subject","")
    score    = evaluation_result.get("score",0)
    total    = evaluation_result.get("total",5)
    pct      = evaluation_result.get("percentage",0)
    focus    = evaluation_result.get("focus","")
    mastered = evaluation_result.get("mastered","")
    nodes    = knowledge_graph.get("nodes",[])

    # 1. AI-generated path
    learning_path = _generate_path(evaluation_result, nodes)

    # Fallback: if Gemini failed, build a simple path from weak nodes
    if not learning_path:
        for i, node in enumerate(sorted(nodes, key=lambda n: (n["status"]!="weak", n["tier"])), 1):
            if node["status"] in ("weak","focus","untouched"):
                learning_path.append({
                    "order": i, "node_id": node["id"], "label": node["label"],
                    "action": "review" if node["status"]=="weak" else "learn",
                    "reason": f"Focus on {node['label']} to improve your {subject} foundation.",
                    "what_to_do": f"Study {node['label']} concepts and practice related exercises.",
                    "status": node["status"], "tier": node["tier"], "accuracy": node.get("accuracy"),
                })
            if len(learning_path) >= 6:
                break

    # 2. Resources for the top struggling/focus topics only
    resource_topics = [
        s["label"] for s in learning_path[:4]
        if s.get("status") in ("weak","focus","untouched")
    ]
    resources = _generate_resources(resource_topics, subject, level)

    # 3. Next quiz
    next_focus = focus
    for step in learning_path:
        if step.get("status") in ("weak","focus"):
            next_focus = step["label"]
            break
    next_level = {"beginner":"intermediate","intermediate":"advanced","advanced":"advanced"}.get(level,"intermediate")

    # 4. Summary
    weak_count = sum(1 for n in nodes if n.get("status")=="weak")
    if pct >= 80:
        summary = f"Excellent — {score}/{total}. You're performing at {level} level. Your path pushes you toward the next tier."
    elif pct >= 50:
        summary = f"Good effort — {score}/{total}. You have {weak_count} gap(s) to address. Your path fixes those first."
    else:
        summary = f"Score: {score}/{total}. Several topics need work. Your path starts exactly where you need it most."

    return {
        "level":         level,
        "summary":       summary,
        "learning_path": learning_path,
        "resources":     resources,
        "next_quiz":     {"subject": subject, "mastered": mastered, "focus": next_focus, "suggested_difficulty": next_level},
    }
