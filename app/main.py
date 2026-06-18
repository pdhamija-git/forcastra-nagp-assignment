from fastapi import FastAPI
from fastapi.responses import JSONResponse
import psycopg2
from psycopg2 import pool as pg_pool
import os
from datetime import datetime, timezone

app = FastAPI()

db_pool = pg_pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=os.environ.get("DB_HOST"),
    port=int(os.environ.get("DB_PORT", 5432)),
    dbname=os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    connect_timeout=3,
)


@app.get("/health")
def health():
    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})
    finally:
        if conn:
            db_pool.putconn(conn)


@app.get("/")
def root():
    return {
        "message": "NAGP Employee API",
        "endpoints": {
            "health": "/health",
            "employees": "/api/employees",
        },
    }


@app.get("/api/employees")
def get_employees():
    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM employees ORDER BY id")
            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        return {"success": True, "count": len(rows), "data": rows}
    except Exception as e:
        print(f"Query error: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": "Database query failed"})
    finally:
        if conn:
            db_pool.putconn(conn)
