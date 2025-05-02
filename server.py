from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from pydantic import BaseModel
from typing import List
import uuid
from datetime import datetime

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    try:
        return psycopg2.connect(
            host='ep-old-frog-a1qfdf29-pooler.ap-southeast-1.aws.neon.tech',
            database='neondb',
            user='neondb_owner',
            password='npg_XH18NuByEtDz'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Pydantic models
class TaskCreate(BaseModel):
    task_name: str
    allocated_time: int

class TaskResponse(BaseModel):
    task_id: str
    task_name: str
    allocated_time: int
    created_at: str

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

class JournalResponse(BaseModel):
    journal_id: str
    title: str
    milestone: str
    content: str
    attachments: List[str]
    created_at: str

class AnalyticsResponse(BaseModel):
    task_id: str
    task_name: str
    total_minutes: int
    allocated_time: int
    created_at: str

# Routes
@app.post("/tasks", response_model=dict)
async def create_task(task: TaskCreate):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        task_id = str(uuid.uuid4())
        created_at = datetime.now()
        cur.execute(
            "INSERT INTO tasks (task_id, task_name, allocated_time, created_at) VALUES (%s, %s, %s, %s)",
            (task_id, task.task_name, task.allocated_time, created_at)
        )
        conn.commit()
        return {"task_id": task_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/tasks", response_model=List[TaskResponse])
async def get_all_tasks():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT task_id, task_name, allocated_time, created_at FROM tasks")
        tasks = [
            {
                "task_id": str(task[0]),
                "task_name": task[1],
                "allocated_time": task[2],
                "created_at": task[3].isoformat()
            }
            for task in cur.fetchall()
        ]
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT task_id, task_name, allocated_time, created_at FROM tasks WHERE task_id = %s",
            (task_id,)
        )
        task = cur.fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return {
            "task_id": str(task[0]),
            "task_name": task[1],
            "allocated_time": task[2],
            "created_at": task[3].isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch task: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.delete("/tasks/{task_id}", response_model=dict)
async def delete_task(task_id: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM timer_logs WHERE task_id = %s", (task_id,))
        cur.execute("DELETE FROM journals WHERE task_id = %s", (task_id,))
        cur.execute("DELETE FROM tasks WHERE task_id = %s", (task_id,))
        conn.commit()
        return {"message": "Task deleted"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.post("/timer_logs", response_model=dict)
async def create_timer_log(log: TimerLogCreate):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        log_id = str(uuid.uuid4())
        start_time = datetime.now()
        end_time = start_time
        cur.execute(
            "INSERT INTO timer_logs (log_id, task_id, start_time, end_time, duration) VALUES (%s, %s, %s, %s, %s)",
            (log_id, log.task_id, start_time, end_time, log.duration)
        )
        conn.commit()
        return {"log_id": log_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create timer log: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.post("/journals", response_model=dict)
async def create_journal(journal: JournalCreate):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        journal_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO journals (journal_id, task_id, title, milestone, content, attachments, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (journal_id, journal.task_id, journal.title, journal.milestone, journal.content, journal.attachments, datetime.now())
        )
        conn.commit()
        return {"journal_id": journal_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create journal: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.put("/journals/{journal_id}", response_model=dict)
async def update_journal(journal_id: str, journal: JournalUpdate):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE journals SET title = %s, milestone = %s, content = %s, attachments = %s WHERE journal_id = %s",
            (journal.title, journal.milestone, journal.content, journal.attachments, journal_id)
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Journal not found")
        conn.commit()
        return {"message": "Journal updated"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update journal: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/journals/{task_id}", response_model=List[JournalResponse])
async def get_journals(task_id: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT journal_id, title, milestone, content, attachments, created_at FROM journals WHERE task_id = %s",
            (task_id,)
        )
        journals = [
            {
                "journal_id": str(j[0]),
                "title": j[1],
                "milestone": j[2],
                "content": j[3],
                "attachments": j[4],
                "created_at": j[5].isoformat()
            }
            for j in cur.fetchall()
        ]
        return journals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch journals: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/journals/details/{journal_id}", response_model=dict)
async def get_journal_details(journal_id: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT title, milestone, content, attachments FROM journals WHERE journal_id = %s",
            (journal_id,)
        )
        journal = cur.fetchone()
        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found")
        return {
            "title": journal[0],
            "milestone": journal[1],
            "content": journal[2],
            "attachments": journal[3]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch journal: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/journals/all", response_model=List[dict])
async def get_all_journals():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT j.journal_id, j.title, j.milestone, j.content, j.attachments, j.created_at, t.task_name
            FROM journals j
            JOIN tasks t ON j.task_id = t.task_id
        """)
        journals = [
            {
                "journal_id": str(j[0]),
                "title": j[1],
                "milestone": j[2],
                "content": j[3],
                "attachments": j[4],
                "created_at": j[5].isoformat(),
                "task_name": j[6]
            }
            for j in cur.fetchall()
        ]
        return journals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch journals: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/analytics", response_model=dict)
async def get_analytics():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.task_id, t.task_name, COALESCE(SUM(tl.duration), 0) as total_minutes, t.allocated_time, t.created_at
            FROM tasks t
            LEFT JOIN timer_logs tl ON t.task_id = tl.task_id
            GROUP BY t.task_id, t.task_name, t.allocated_time, t.created_at
        """)
        tasks = [
            {
                "task_id": str(t[0]),
                "task_name": t[1],
                "total_minutes": t[2],
                "allocated_time": t[3],
                "created_at": t[4].isoformat()
            }
            for t in cur.fetchall()
        ]
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/analytics/{task_id}", response_model=dict)
async def get_task_analytics(task_id: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(tl.duration), 0) as total_minutes, t.allocated_time, t.created_at
            FROM tasks t
            LEFT JOIN timer_logs tl ON t.task_id = tl.task_id
            WHERE t.task_id = %s
            GROUP BY t.task_id, t.allocated_time, t.created_at
        """, (task_id,))
        analytics = cur.fetchone()
        if not analytics:
            raise HTTPException(status_code=404, detail="Task not found")
        return {
            "total_minutes": analytics[0],
            "allocated_time": analytics[1],
            "created_at": analytics[2].isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")
    finally:
        cur.close()
        conn.close()
