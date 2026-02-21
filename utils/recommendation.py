def recommend(performance):
    if performance == "Low":
        return [
            "Start with basic concepts",
            "Use beginner-friendly video tutorials",
            "Practice simple quizzes daily"
        ]
    elif performance == "Medium":
        return [
            "Revise weak areas",
            "Practice mixed-level problems",
            "Move gradually to advanced topics"
        ]
    else:
        return [
            "Skip basic topics",
            "Focus on advanced problem solving",
            "Try project-based learning"
        ]
