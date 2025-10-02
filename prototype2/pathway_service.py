import google.generativeai as genai
import sqlite3
import json
import os

# --- IMPORTANT: Configure with your API Key ---
# It's best practice to use environment variables for keys.
# For now, you can paste it directly.
API_KEY = "AIzaSyC7hVo8CcVWhND82BsFrgCKOP8uydEuMEM"
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    model = None

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_user_pathway(user_id):
    """Retrieves the latest pathway for a user from the database."""
    conn = get_db_connection()
    pathway_row = conn.execute(
        'SELECT pathway_data FROM pathways WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
        (user_id,)
    ).fetchone()
    conn.close()
    if pathway_row:
        return json.loads(pathway_row['pathway_data'])
    return None

def save_user_pathway(user_id, pathway_data):
    """Saves a new pathway for a user to the database."""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO pathways (user_id, pathway_data) VALUES (?, ?)',
        (user_id, json.dumps(pathway_data))
    )
    conn.commit()
    conn.close()

def generate_new_pathway(user_data, user_aspiration):
    """Generates a new pathway using the LLM."""
    if not model:
        print("LLM Model not available. Returning mock data.")
        # Fallback to mock data if API key is invalid or missing
        with open('pathway_data.json', 'r') as f:
            return json.load(f)

    # In a real app, you'd pull this from your 'courses' table
    mock_course_data = """
    - IT Fundamentals & Web Basics (NSQF Level 3)
    - Programming with JavaScript (NSQF Level 4)
    - Frontend Frameworks with React (NSQF Level 4)
    - Backend Development with Node.js (NSQF Level 5)
    - Cloud Engineering on AWS (NSQF Level 5)
    - Advanced Data Science with Python (NSQF Level 6)
    - UI/UX Design Fundamentals (NSQF Level 4)
    """

    prompt = f"""
    You are an expert career counselor for students in India, specializing in the NSQF framework. Your task is to create a personalized, step-by-step learning pathway.

    **User Profile:**
    - Stated Aspiration: "{user_aspiration}"
    - General Interests: "{user_data['interests']}"
    - Current Skills/Achievements: "{user_data['achievements']}"
    - Age: {user_data['study_age']}

    **Available NSQF Aligned Courses:**
    {mock_course_data}

    **Your Task:**
    1.  Analyze the user's profile and aspiration.
    2.  Select a sequence of 3-5 courses from the available list to create a logical learning path.
    3.  The pathway must be progressive, starting with lower NSQF levels and moving to higher ones.
    4.  Mark the first step's status as "in_progress" and all others as "not_started".
    5.  Return the pathway ONLY in a strict JSON format. Do not include any explanation or markdown.

    **JSON Output Format:**
    {{
      "pathway_title": "The specific career goal, e.g., Junior Web Developer",
      "steps": [
        {{
          "nsqf_level": 3,
          "title": "Course Title from list",
          "description": "A brief, one-sentence description of why this course is the first step.",
          "skills": ["Skill 1", "Skill 2"],
          "status": "in_progress"
        }},
        {{
          "nsqf_level": 4,
          "title": "Next Course Title",
          "description": "Description of the next step.",
          "skills": ["Skill 3", "Skill 4"],
          "status": "not_started"
        }}
      ]
    }}
    """

    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"Error generating pathway from LLM: {e}")
        # Fallback to mock data on API error
        with open('pathway_data.json', 'r') as f:
            return json.load(f)
