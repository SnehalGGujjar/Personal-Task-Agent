import streamlit as st
import json
import os
from datetime import datetime, timedelta

# === Groq API Setup ===
try:
    from groq import Groq
    # Read API key from key.txt and pass it directly
    with open("key.txt") as f:
        API_KEY = f.read().strip()

    client = Groq(api_key=API_KEY)  # Correct way to pass API key
    model_name = "llama-3.1-8b-instant"
    ai_available = True
except Exception as e:
    st.warning(f"Groq client not available: {e}")
    ai_available = False

# === Task File ===
TASK_FILE = "tasks_agentic.json"

# === Load/Save Functions ===
def load_tasks():
    if os.path.exists(TASK_FILE):
        try:
            with open(TASK_FILE, "r") as f:
                tasks = json.load(f)
        except:
            tasks = []
    else:
        tasks = []
    return tasks

def save_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

# === Session State ===
if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "delete_trigger" not in st.session_state:
    st.session_state.delete_trigger = False  # Toggle to refresh UI after deletion

# === Helpers ===
def sort_tasks(tasks):
    priority_order = {"High": 1, "Medium": 2, "Low": 3}
    return sorted(tasks, key=lambda x: (priority_order.get(x["priority"], 4), x["deadline"]))

def upcoming_alerts(tasks):
    alerts = []
    today = datetime.now().date()
    for t in tasks:
        try:
            deadline = datetime.strptime(t["deadline"], "%Y-%m-%d").date()
            if 0 <= (deadline - today).days <= 1:
                alerts.append(f"⚠️ {t['title']} is due {t['deadline']}")
        except:
            continue
    return alerts

# === Streamlit UI ===
st.title("🧠 Agentic Task Planner")
st.write("Add tasks, view calendar, and get AI suggestions")

# --- Add Task ---
with st.expander("🆕 Add New Task"):
    title = st.text_input("Task Title")
    deadline = st.date_input("Deadline")
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    notes = st.text_area("Notes")
    if st.button("Add Task"):
        if title:
            st.session_state.tasks.append({
                "title": title,
                "deadline": deadline.strftime("%Y-%m-%d"),
                "priority": priority,
                "notes": notes
            })
            st.success("Task added!")
            save_tasks(st.session_state.tasks)

# --- Display Tasks ---
st.subheader("📋 Task Calendar / Table")
if st.session_state.tasks:
    sorted_tasks = sort_tasks(st.session_state.tasks)
    for i, t in enumerate(sorted_tasks):
        with st.expander(f"{t['title']} - {t['priority']} - Due {t['deadline']}"):
            st.write(f"Notes: {t['notes']}")
            if st.button(f"Delete {t['title']}", key=f"del_{i}"):
                st.session_state.tasks.remove(t)
                save_tasks(st.session_state.tasks)
                # Toggle trigger to refresh UI
                st.session_state.delete_trigger = not st.session_state.delete_trigger
                st.experimental_rerun()
else:
    st.write("No tasks added yet!")

# --- Alerts ---
alerts = upcoming_alerts(st.session_state.tasks)
for a in alerts:
    st.warning(a)

# --- AI Suggested Plan ---
st.subheader("🤖 Generate AI Suggested Plan")
if st.button("Generate AI Plan"):
    if not ai_available:
        st.error("Groq AI not available. Check your API key or package.")
    else:
        tasks_text = json.dumps(st.session_state.tasks, indent=2)
        messages = [
            {"role": "system", "content": "You are a personal assistant AI. Organize tasks and suggest a plan."},
            {"role": "user", "content": f"My tasks:\n{tasks_text}\nPlease suggest a plan."}
        ]
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=False
            )
            plan_text = completion.choices[0].message.content
            st.text_area("AI Suggested Plan", plan_text, height=200)
        except Exception as e:
            st.error(f"Error generating plan: {e}")

# --- Chat with AI ---
st.subheader("💬 Chat with AI about your tasks")
user_input = st.text_input("Ask AI something about your tasks")
if st.button("Send", key="chat_send"):
    if user_input and ai_available:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=st.session_state.chat_history,
                stream=False
            )
            ai_message = response.choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": ai_message})
            st.text_area("AI Response", ai_message, height=150)
        except Exception as e:
            st.error(f"Error: {e}")
