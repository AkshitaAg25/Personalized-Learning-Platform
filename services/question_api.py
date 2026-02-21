import requests
import html
import random

def fetch_questions(amount=5, category=None, difficulty=None):
    url = "https://opentdb.com/api.php"

    params = {
        "amount": amount,
        "type": "multiple"
    }

    if category:
        params["category"] = category
    if difficulty:
        params["difficulty"] = difficulty

    response = requests.get(url, params=params)
    data = response.json()

    # ✅ SAFETY CHECK
    if data.get("response_code") != 0 or "results" not in data:
        return []

    questions = []

    for item in data["results"]:
        options = item["incorrect_answers"] + [item["correct_answer"]]
        random.shuffle(options)

        questions.append({
            "question": html.unescape(item["question"]),
            "options": [html.unescape(opt) for opt in options],
            "answer": html.unescape(item["correct_answer"])
        })

    return questions
