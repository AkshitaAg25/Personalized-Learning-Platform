def evaluate(user_answers, correct_answers):
    score = 0

    for user, correct in zip(user_answers, correct_answers):
        if user.strip().lower() == correct.strip().lower():
            score += 1

    if score == len(correct_answers):
        return "High"
    elif score >= len(correct_answers) // 2:
        return "Medium"
    else:
        return "Low"
