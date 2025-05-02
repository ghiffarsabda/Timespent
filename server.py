from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from pydantic import BaseModel
from typing import List
import uuid
from datetime import datetime

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host='ep-old-frog-a1qfdf29-pooler.ap-southeast-1.aws.neon.tech',
        database='neondb',
        user='neondb_owner',
        password='npg_XH18NuByEtDz'
    )

# Pydantic models
class TaskCreate(BaseModel):
    task_name: str
    allocated_time: int

class TimerLogCreate(BaseModel):
    task_id: str
    duration: int

class JournalCreate(BaseModel):
    task_id: str
    title: str
    milestone: str
    content: str
    attachments: List[str]

class JournalUpdate(BaseModel):
    title: str
    milestone: str
    content: str
    attachments: List[str]

# Routes
@app.get("/tasks")
async def get_tasks():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT task_id, task_name, allocated_time FROM tasks")
    tasks = [{"task_id": str(t[0]), "task_name": t[1], "allocated_time": t[2]} for t in cur.fetchall()]
    cur.close()
    conn.close()
    return tasks

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT task_id, task_name, allocated_time FROM tasks WHERE task_id = %s", (task_id,))
    task = cur.fetchone()
    cur.close()
    conn.close()
    return {"task_id": str(task[0]), "task_name": task[1], "allocated_time": task[2]}

@app.post("/tasks")
async def create_task(task: TaskCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    task_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO tasks (task_id, task_name, allocated_time) VALUES (%s, %s, %s)",
        (task_id, task.task_name, task.allocated_time)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"task_id": task_id}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM timer_logs WHERE task_id = %s", (task_id,))
    cur.execute("DELETE FROM journals WHERE task_id = %s", (task_id,))
    cur.execute("DELETE FROM tasks WHERE task_id = %s", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Task deleted"}

@app.post("/timer_logs")
async def create_timer_log(log: TimerLogCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    log_id = str(uuid.uuid4())
    start_time = datetime.now()
    end_time = start_time
    cur.execute(
        "INSERT INTO timer_logs (log_id, task_id, start_time, end_time, duration) VALUES (%s, %s, %s, %s, %s)",
        (log_id, log.task_id, start_time, end_time, log.duration)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"log_id": log_id}

@app.post("/journals")
async def create_journal(journal: JournalCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    journal_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO journals (journal_id, task_id, title, milestone, content, attachments) VALUES (%s, %s, %s, %s, %s, %s)",
        (journal_id, journal.task_id, journal.title, journal.milestone, journal.content, journal.attachments)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"journal_id": journal_id}

@app.put("/journals/{journal_id}")
async def update_journal(journal_id: str, journal: JournalUpdate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE journals SET title = %s, milestone = %s, content = %s, attachments = %s WHERE journal_id = %s",
        (journal.title, journal.milestone, journal.content, journal.attachments, journal_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Journal updated"}

@app.get("/journals/{task_id}")
async def get_journals(task_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT journal_id, title, milestone, content, attachments, created_at FROM journals WHERE task_id = %s", (task_id,))
    journals = [{"journal_id": str(j[0]), "title": j[1], "milestone": j[2], "content": j[3], "attachments": j[4], "created_at": j[5]} for j in cur.fetchall()]
    cur.close()
    conn.close()
    return journals

@app.get("/journals/details/{journal_id}")
async def get_journal_details(journal_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT title, milestone, content, attachments FROM journals WHERE journal_id = %s", (journal_id,))
    journal = cur.fetchone()
    cur.close()
    conn.close()
    return {"title": journal[0], "milestone": journal[1], "content": journal[2], "attachments": journal[3]}

@app.get("/journals/all")
async def get_all_journals():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT j.journal_id, j.title, j.milestone, j.content, j.attachments, j.created_at, t.task_name
        FROM journals j
        JOIN tasks t ON j.task_id = t.task_id
    """)
    journals = [{"journal_id": str(j[0]), "title": j[1], "milestone": j[2], "content": j[3], "attachments": j[4], "created_at": j[5], "task_name": j[6]} for j in cur.fetchall()]
    cur.close()
    conn.close()
    return journals

@app.get("/analytics")
async def get_analytics():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.task_id, t.task_name, COALESCE(SUM(tl.duration), 0) as total_minutes, t.allocated_time - COALESCE(SUM(tl.duration), 0) as debt
        FROM tasks t
        LEFT JOIN timer_logs tl ON t.task_id = tl.task_id
        GROUP BY t.task_id, t.task_name, t.allocated_time
    """)
    tasks = [{"task_id": str(t[0]), "task_name": t[1], "total_minutes": t[2], "debt": t[3]} for t in cur.fetchall()]
    cur.close()
    conn.close()
    return {"tasks": tasks}

@app.get("/analytics/{task_id}")
async def get_task_analytics(task_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(tl.duration), 0) as total_minutes, t.allocated_time - COALESCE(SUM(tl.duration), 0) as debt
        FROM tasks t
        LEFT JOIN timer_logs tl ON t.task_id = tl.task_id
        WHERE t.task_id = %s
        GROUP BY t.task_id, t.allocated_time
    """, (task_id,))
    analytics = cur.fetchone()
    cur.close()
    conn.close()
    return {"total_minutes": analytics[0], "debt": analytics[1]}