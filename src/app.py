"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import sqlite3

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Database path
db_path = os.path.join(current_dir, "activities.db")

def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        description TEXT,
        schedule TEXT,
        max_participants INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE,
        name TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE,
        password_hash TEXT,
        role TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS signups (
        id INTEGER PRIMARY KEY,
        activity_name TEXT,
        email TEXT,
        FOREIGN KEY(activity_name) REFERENCES activities(name)
    )''')
    # Insert initial activities if not exist
    initial_activities = [
        ("Chess Club", "Learn strategies and compete in chess tournaments", "Fridays, 3:30 PM - 5:00 PM", 12),
        ("Programming Class", "Learn programming fundamentals and build software projects", "Tuesdays and Thursdays, 3:30 PM - 4:30 PM", 20),
        ("Gym Class", "Physical education and sports activities", "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM", 30),
        ("Soccer Team", "Join the school soccer team and compete in matches", "Tuesdays and Thursdays, 4:00 PM - 5:30 PM", 22),
        ("Basketball Team", "Practice and play basketball with the school team", "Wednesdays and Fridays, 3:30 PM - 5:00 PM", 15),
        ("Art Club", "Explore your creativity through painting and drawing", "Thursdays, 3:30 PM - 5:00 PM", 15),
        ("Drama Club", "Act, direct, and produce plays and performances", "Mondays and Wednesdays, 4:00 PM - 5:30 PM", 20),
        ("Math Club", "Solve challenging problems and participate in math competitions", "Tuesdays, 3:30 PM - 4:30 PM", 10),
        ("Debate Team", "Develop public speaking and argumentation skills", "Fridays, 4:00 PM - 5:30 PM", 12)
    ]
    for name, desc, sched, max_p in initial_activities:
        c.execute("INSERT OR IGNORE INTO activities (name, description, schedule, max_participants) VALUES (?, ?, ?, ?)", (name, desc, sched, max_p))
    # Insert initial signups
    initial_signups = [
        ("Chess Club", "michael@mergington.edu"),
        ("Chess Club", "daniel@mergington.edu"),
        ("Programming Class", "emma@mergington.edu"),
        ("Programming Class", "sophia@mergington.edu"),
        ("Gym Class", "john@mergington.edu"),
        ("Gym Class", "olivia@mergington.edu"),
        ("Soccer Team", "liam@mergington.edu"),
        ("Soccer Team", "noah@mergington.edu"),
        ("Basketball Team", "ava@mergington.edu"),
        ("Basketball Team", "mia@mergington.edu"),
        ("Art Club", "amelia@mergington.edu"),
        ("Art Club", "harper@mergington.edu"),
        ("Drama Club", "ella@mergington.edu"),
        ("Drama Club", "scarlett@mergington.edu"),
        ("Math Club", "james@mergington.edu"),
        ("Math Club", "benjamin@mergington.edu"),
        ("Debate Team", "charlotte@mergington.edu"),
        ("Debate Team", "henry@mergington.edu")
    ]
    for act, email in initial_signups:
        c.execute("INSERT OR IGNORE INTO signups (activity_name, email) VALUES (?, ?)", (act, email))
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name, description, schedule, max_participants FROM activities")
    rows = c.fetchall()
    result = {}
    for row in rows:
        name, desc, sched, max_p = row
        # Get participants
        c.execute("SELECT email FROM signups WHERE activity_name = ?", (name,))
        participants = [r[0] for r in c.fetchall()]
        result[name] = {
            "description": desc,
            "schedule": sched,
            "max_participants": max_p,
            "participants": participants
        }
    conn.close()
    return result


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Check if activity exists
    c.execute("SELECT max_participants FROM activities WHERE name = ?", (activity_name,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Activity not found")
    max_p = row[0]
    # Check current participants count
    c.execute("SELECT COUNT(*) FROM signups WHERE activity_name = ?", (activity_name,))
    count = c.fetchone()[0]
    if count >= max_p:
        conn.close()
        raise HTTPException(status_code=400, detail="Activity is full")
    # Check if already signed up
    c.execute("SELECT 1 FROM signups WHERE activity_name = ? AND email = ?", (activity_name, email))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Student is already signed up")
    # Add student
    c.execute("INSERT INTO signups (activity_name, email) VALUES (?, ?)", (activity_name, email))
    conn.commit()
    conn.close()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Check if activity exists
    c.execute("SELECT 1 FROM activities WHERE name = ?", (activity_name,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Activity not found")
    # Check if signed up
    c.execute("SELECT 1 FROM signups WHERE activity_name = ? AND email = ?", (activity_name, email))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")
    # Remove
    c.execute("DELETE FROM signups WHERE activity_name = ? AND email = ?", (activity_name, email))
    conn.commit()
    conn.close()
    return {"message": f"Unregistered {email} from {activity_name}"}
