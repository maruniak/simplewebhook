from fastapi import FastAPI, Request, HTTPException, Response, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import urllib.parse
import base64
import os
from dotenv import load_dotenv
import hashlib
import hmac
import httpx

# ------------------------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------------------------
load_dotenv()

NEED_REDIRECT = os.getenv("NEED_REDIRECT", "false").lower() == "true"
REDIRECTION_URL = os.getenv("REDIRECTION_URL", "")
ENABLE_PROTECT = os.getenv("ENABLE_PROTECT", "false").lower() == "true"
ALLOWED_IPS = os.getenv("ALLOWED_IP", "").split(",")
SECRET_KEY_PATH = os.getenv("SECRET_KEY_PATH", "./certs/test-server.cert")

# ------------------------------------------------------------------------------
# Database setup
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# FastAPI application
# ------------------------------------------------------------------------------
app = FastAPI()

# ------------------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------------------
def is_ip_allowed(client_ip: str) -> bool:
    """Check if the client's IP is allowed."""
    return client_ip in ALLOWED_IPS

def verify_signature(data: str, signature: str) -> bool:
    """Validate the signature of the incoming request."""
    try:
        # For demonstration, we "pretend" to read a public key and compare a signature
        public_key = open(SECRET_KEY_PATH, "rb").read()
        decoded_signature = base64.b64decode(signature)
        valid = hmac.compare_digest(data, decoded_signature)
        return valid
    except Exception as e:
        print(f"DEBUG: Signature verification failed: {e}")
        return False

def generate_response(action: str, reason: str = "", forward_url: str = "") -> str:
    """Generate the required response format in plain text."""
    response_lines = [
        f"Response.action={action}",
        f"Response.reason={reason}",
        f"Response.forwardUrl={forward_url}",
    ]
    return "\n".join(response_lines) + "\n"

# ------------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------------
@app.middleware("http")
async def ip_protection_middleware(request: Request, call_next):
    """Middleware to enforce IP protection if enabled."""
    if ENABLE_PROTECT:
        client_ip = request.client.host
        if not is_ip_allowed(client_ip):
            print(f"DEBUG: IP {client_ip} is not allowed.")
            raise HTTPException(status_code=403, detail="Access forbidden")
    return await call_next(request)

# ------------------------------------------------------------------------------
# Forwarding function (used in background)
# ------------------------------------------------------------------------------
async def forward_in_background(
    data: dict,  # Already parsed POST data
    headers: dict,
    log_id: int,
    url: str
):
    """Forward the request to the external URL in the background."""
    print("DEBUG (BG): Entering forward_in_background()")
    print(f"DEBUG (BG): Forwarding to {url}")

    # Convert the parsed_data back to x-www-form-urlencoded
    form_body = []
    for k, v in data.items():
        form_body.append(f"{k}={v[0]}")
    encoded_body = "&".join(form_body)

    # Perform the HTTP call
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url=url,
                headers=headers,
                content=encoded_body
            )
            print(f"DEBUG (BG): External server returned status: {response.status_code}")
            print(f"DEBUG (BG): External server returned body: {response.text}")

            # Update log to indicate success/failure
            db = SessionLocal()
            try:
                entry = db.query(Log).filter(Log.id == log_id).first()
                if entry:
                    entry.body += f" | BG Redirect: {response.status_code}"
                db.commit()
            finally:
                db.close()

        except httpx.RequestError as e:
            print(f"ERROR (BG): BG forward request error => {e}")
            db = SessionLocal()
            try:
                entry = db.query(Log).filter(Log.id == log_id).first()
                if entry:
                    entry.body += f" | BG Redirect Failed: {str(e)}"
                db.commit()
            finally:
                db.close()

# ------------------------------------------------------------------------------
# Main POST endpoint
# ------------------------------------------------------------------------------
@app.post("/testcallback2")
async def handle_post(request: Request, background_tasks: BackgroundTasks):
    print("DEBUG: Received a POST request on /testcallback2")

    # Read raw body
    raw_body = await request.body()
    print(f"DEBUG: Raw body: {raw_body}")

    # Parse the request data
    try:
        parsed_data = urllib.parse.parse_qs(raw_body.decode("utf-8"))
        print(f"DEBUG: Parsed data => {parsed_data}")
    except Exception as e:
        print(f"ERROR: Could not parse body => {e}")
        return PlainTextResponse("Error parsing body", status_code=400)

    # Log the request in the database
    db = SessionLocal()
    log_id = None
    try:
        log_entry = Log(method="POST", time=datetime.now(), body=str(parsed_data))
        db.add(log_entry)
        db.commit()
        log_id = log_entry.id
        print(f"DEBUG: Saved log entry with id {log_id}")
    except Exception as e:
        print(f"ERROR: Failed to save log entry => {e}")
    finally:
        db.close()

    # Always build the local response first
    # (The Payment Gateway sees this response no matter what)
    response_action = "approve"
    response_reason = "ok"
    response_forward_url = ""

    # Construct plain text response from the parsed_data
    response_lines = []
    for key, value in parsed_data.items():
        response_lines.append(f"{key}={value[0]}")

    response_lines.append(f"Response.action={response_action}")
    response_lines.append(f"Response.reason={response_reason}")
    response_lines.append(f"Response.forwardUrl={response_forward_url}")

    response_text = "\n".join(response_lines)
    print("DEBUG: Final local response to the gateway:")
    print(response_text)

    # If we need to forward in the background, do so after returning a local response
    if NEED_REDIRECT and REDIRECTION_URL:
        print("DEBUG: Scheduling background task for redirection...")
        # We can re-use request headers, but remove 'host'
        new_headers = dict(request.headers)
        new_headers.pop("host", None)

        # Add the background task
        background_tasks.add_task(
            forward_in_background,
            data=parsed_data,
            headers=new_headers,
            log_id=log_id,
            url=REDIRECTION_URL
        )

    # Return local response IMMEDIATELY
    return PlainTextResponse(content=response_text)

# ------------------------------------------------------------------------------
# GET endpoint
# ------------------------------------------------------------------------------
@app.get("/testcallback2")
async def handle_get(request: Request):
    print("DEBUG: Received a GET request on /testcallback2")

    db = SessionLocal()
    try:
        log_entry = Log(method="GET", time=datetime.now(), body="Request received")
        db.add(log_entry)
        db.commit()
        print("DEBUG: Logged GET request.")
    finally:
        db.close()

    return PlainTextResponse("GET requests are not processed for this endpoint.", status_code=405)

# ------------------------------------------------------------------------------
# Additional Endpoints (Logs, Page, Clear Logs)
# ------------------------------------------------------------------------------
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
