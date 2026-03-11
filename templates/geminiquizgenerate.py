from google import genai
from google.genai import types
import json

client = genai.Client(api_key="AIzaSyA1oqF9bFoWXpt9iRo_5dPM42CNnre3dsk")

def fetch_questions_gemini(subject, mastered, focus, amount=5):
    model_name = "gemini-2.5-flash"
    
    prompt = f"""
    Create a {amount}-question multiple choice quiz about {subject}.
    The user has already mastered: {mastered}.
    The user wants to focus on: {focus}. The quiz is to analyze user performance so generate question accordingly.
    Return the output ONLY as a JSON list of objects with "question", 
    "options" (list of 4 strings), and "answer".
    """
    
    #generating content
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    
    # cleaning the response
    cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
    
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        return []