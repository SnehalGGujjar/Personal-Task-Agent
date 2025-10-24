import streamlit as st
import json
from datetime import datetime, timedelta
import os

# --- Groq Setup ---
from groq import Groq

# Load API key from key.txt
with open("key.txt") as f:
    GROQ_API_KEY = f.read().strip()

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = "openai/gpt-oss-20b"  # Use a valid model from your Groq console

# --- Task Storage ---
TASK_FILE = "tasks.json"

def load_tasks():
    try:
        with open(TASK_FILE, "r") as f:
            tasks = json.load(f)
            return tasks
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        # Convert deadlines to string if they are datetime objects
        for t in tasks:
            if isinstance(t['deadline'], str):
                continue
            if isinstance(t['deadline'], datetime):
                t['deadline'] = t['deadline'].strftime("%Y-%m-%d")
        json.dump(tasks, f, indent=4)

# --- Initialize Session State ---
if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

# --- UI ---
st.title("🧠 Agentic Task Planner")
st.subheader("Add tasks, view calendar, and get AI suggestions")

# --- Task Input Form ---
with st.form("task_form"):
    title = st.text_input("Task Title")
    deadline = st.date_input("Deadline", value=datetime.today())
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    notes = st.text_area("Notes")
    submitted = st.form_submit_button("Add Task")
    
    if submitted:
        task = {
            "title": title if title else "Untitled Task",
            "deadline": deadline.strftime("%Y-%m-%d"),
            "priority": priority,
            "notes": notes
        }
        st.session_state.tasks.append(task)
        save_tasks(st.session_state.tasks)
        st.success("Task added!")

# --- Task Table / Calendar View ---
st.subheader("📋 Task Calendar / Table")
if st.session_state.tasks:
    sorted_tasks = sorted(
        st.session_state.tasks,
        key=lambda x: ({"High": 1, "Medium": 2, "Low": 3}[x['priority']], x['deadline'])
    )
    for t in sorted_tasks:
        expander_label = f"{t['title']} - {t['priority']} - Due {t['deadline']}"
        with st.expander(expander_label):
            st.write(f"Notes: {t['notes']}")
            # Delete button
            if st.button(f"Delete '{t['title']}'"):
                st.session_state.tasks.remove(t)
                save_tasks(st.session_state.tasks)
                st.experimental_rerun()

    # Upcoming task alerts
    st.subheader("⚠️ Upcoming Tasks within 1 day!")
    today = datetime.today().date()
    for t in st.session_state.tasks:
        t_deadline = datetime.strptime(t['deadline'], "%Y-%m-%d").date()
        if 0 <= (t_deadline - today).days <= 1:
            st.warning(f"{t['title']} - {t['priority']} - Due {t['deadline']}")

else:
    st.info("No tasks added yet!")

# --- AI Suggested Plan ---
st.subheader("🤖 Generate AI Suggested Plan")
if st.button("Generate AI Plan"):
    try:
        prompt = f"""
You are an AI task planner. Organize these tasks by priority and urgency:
{json.dumps(st.session_state.tasks, indent=2)}
Provide a clear daily plan in bullet points.
"""
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        plan = response.choices[0].message.content
        st.text_area("AI Suggested Plan", plan, height=300)
    except Exception as e:
        st.error(f"Error generating plan: {e}")
