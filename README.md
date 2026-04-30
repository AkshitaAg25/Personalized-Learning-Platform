# Personalized Learning Platform (Mind Map)

An AI-powered web application that identifies knowledge gaps, generates adaptive quizzes, and creates personalized learning paths for students.

---

## Overview

The **Personalized Learning Platform** is designed to overcome the limitations of one-size-fits-all learning systems. It analyzes user performance at a **topic level**, detects weak areas, and generates a structured, AI-driven learning path tailored to each learner.

Built using **Flask** and **Google Gemini API**, the platform integrates assessment, feedback, and recommendations into a single lightweight web application.

---

## Features

-  **AI Quiz Generation**
  - Dynamically generates MCQs based on subject, focus area, and prior knowledge
  - Powered by Gemini 2.5 Flash

-  **Topic-Level Evaluation**
  - Tracks accuracy per topic instead of overall score
  - Identifies strong and weak areas precisely

-  **Knowledge Graph**
  - Represents relationships between topics
  - Shows prerequisites and related concepts

-  **Personalized Learning Path**
  - Step-by-step roadmap (review → learn → practice → challenge)
  - Tailored to individual performance

-  **Progress Dashboard**
  - Stores quiz history
  - Tracks improvement over time

-  **User Authentication**
  - Secure login and registration system

---

## Tech Stack

**Frontend**
- HTML
- CSS
- Jinja2 Templates

**Backend**
- Python
- Flask

**Database**
- SQLite

**AI Integration**
- Google Gemini 2.5 Flash API

**Other Tools**
- Gunicorn (for deployment)
- Render (hosting)

---

##  Project Structure
```Personalized-Learning-Platform/
.
├── app.py
├── utils/
│   ├── auth.py
│   ├── evaluation.py
│   ├── init_db.py
│   ├── knowledge_graph.py
│   └── recommendation.py
├── services/
│   ├── geminiquizgenerate.py
│   └── question_api.py
├── templates/
├── static/
├── database.db
└── requirements.txt
```

##  Workflow
1. User registers or logs in  
2. Inputs subject, focus area, and known topics  
3. AI generates a personalized quiz  
4. System evaluates responses  
5. Knowledge gaps are identified  
6. Learning path is generated  
7. Data is stored and displayed on the dashboard  

## Future Improvements
1. Student collaboration feature.
2. Gamification elements.
3. Advanced analytics and instructor dashboard.


##  Authors
Akshita Agarwal  
Jagrati Maheshwari
