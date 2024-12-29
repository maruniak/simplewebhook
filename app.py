from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import urllib.parse

# Database setup
DATABASE_URL = "sqlite:///./data/logs.db"  # Ensure the path matches the mounted volume

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

@app.get("/testcallback2")
def read_test():
    db = SessionLocal()
    log = Log(method="GET", body=None)
    db.add(log)
    db.commit()
    db.refresh(log)
    db.close()
    return {"message": "GET request success"}

@app.post("/testcallback2")
async def create_test(request: Request):
    raw_body = await request.body()
    body_str = raw_body.decode('utf-8')
    parsed_data = urllib.parse.parse_qs(body_str)

    db = SessionLocal()
    log = Log(method="POST", body=str(parsed_data))
    db.add(log)
    db.commit()
    db.refresh(log)
    db.close()
    return {"received_data": parsed_data}

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