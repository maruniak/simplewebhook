from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, FileResponse
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import urllib.parse
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
NEED_REDIRECT = os.getenv("NEED_REDIRECT", "false").lower() == "true"
REDIRECTION_URL = os.getenv("REDIRECTION_URL", "")
ENABLE_PROTECT = os.getenv("ENABLE_PROTECT", "false").lower() == "true"
ALLOWED_IPS = os.getenv("ALLOWED_IP", "").split(",")

# Database setup
DATABASE_URL = "sqlite:///./data/logs.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    method = Column(String, index=True)
    time = Column(DateTime, default=datetime.now)
    body = Column(String)

Base.metadata.create_all(bind=engine)

app = FastAPI()

def is_ip_allowed(client_ip: str) -> bool:
    """Check if the client's IP is allowed."""
    return client_ip in ALLOWED_IPS

@app.middleware("http")
async def ip_protection_middleware(request: Request, call_next):
    """Middleware to enforce IP protection if enabled."""
    if ENABLE_PROTECT:
        client_ip = request.client.host
        if not is_ip_allowed(client_ip):
            raise HTTPException(status_code=403, detail="Access forbidden")
    return await call_next(request)

async def forward_request_to_url(request: Request, url: str):
    """Forward the incoming request to another URL."""
    async with httpx.AsyncClient() as client:
        # Forward headers
        headers = dict(request.headers)
        
        # Forward the body
        body = await request.body()
        
        # Send the request to the redirection URL
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.headers.get("Content-Type") == "application/json" else response.text
        )

@app.post("/testcallback2")
async def handle_post(request: Request):
    if NEED_REDIRECT and REDIRECTION_URL and request.client.host not in ["127.0.0.1", "localhost"]:
        return await forward_request_to_url(request, REDIRECTION_URL)

    # Process POST request and log to the database
    raw_body = await request.body()
    parsed_data = urllib.parse.parse_qs(raw_body.decode("utf-8"))

    # Save log to the database
    db = SessionLocal()
    try:
        log_entry = Log(method="POST", time=datetime.now(), body=str(parsed_data))
        db.add(log_entry)
        db.commit()
    finally:
        db.close()

    return {"received_data": parsed_data}

@app.get("/testcallback2")
async def handle_get(request: Request):
    if NEED_REDIRECT and REDIRECTION_URL and request.client.host not in ["127.0.0.1", "localhost"]:
        return await forward_request_to_url(request, REDIRECTION_URL)

    # Save log to the database
    db = SessionLocal()
    try:
        log_entry = Log(method="GET", time=datetime.now(), body=None)
        db.add(log_entry)
        db.commit()
    finally:
        db.close()

    return {"message": "GET request success"}


@app.get("/testcallback2/logs")
def get_logs():
    db = SessionLocal()
    logs = db.query(Log).order_by(Log.time.desc()).all()
    db.close()
    return [{"method": log.method, "time": log.time, "body": log.body} for log in logs]

@app.get("/testcallback2/logs/recent")
def get_recent_logs():
    db = SessionLocal()
    logs = db.query(Log).order_by(Log.time.desc()).limit(10).all()
    db.close()
    return [{"method": log.method, "time": log.time, "body": log.body} for log in logs]

@app.get("/testcallback2/logs/full")
def get_full_logs():
    db = SessionLocal()
    logs = db.query(Log).order_by(Log.time.desc()).all()
    db.close()
    return [{"method": log.method, "time": log.time, "body": log.body} for log in logs]

@app.get("/testcallback2/page", response_class=HTMLResponse)
def get_page():
    return FileResponse("index.html")

@app.delete("/testcallback2/logs/clear")
def clear_logs():
    db = SessionLocal()
    try:
        db.query(Log).delete()  # Delete all logs
        db.commit()
        return {"message": "Logs cleared successfully"}
    finally:
        db.close()
