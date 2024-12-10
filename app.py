from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime
import json

app = FastAPI()

# Global in-memory logs list
logs = []

@app.get("/testcallback2")
def read_test():
    # Log the GET request
    logs.append({
        "method": "GET",
        "time": datetime.now().isoformat(),
        "body": None
    })
    return {"message": "GET request success"}

@app.post("/testcallback2")
async def create_test(request: Request):
    data = await request.json()
    # Log the POST request with its data
    logs.append({
        "method": "POST",
        "time": datetime.now().isoformat(),
        "body": data
    })
    return {"received_data": data}

@app.get("/testcallback2/page", response_class=HTMLResponse)
def get_page():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Test Callback Page</h1>
        <button onclick="getData()">Get Data (GET)</button>
        <button onclick="postData()">Post Data (POST)</button>
        <button onclick="showLogs()">Show Logs</button>
        <div id="response"></div>
        <div id="logsArea"></div>
        <script>
            async function getData() {
                const resp = await fetch('/testcallback2');
                const json = await resp.json();
                document.getElementById('response').innerText = JSON.stringify(json, null, 2);
            }

            async function postData() {
                const resp = await fetch('/testcallback2', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({foo: 'bar'})
                });
                const json = await resp.json();
                document.getElementById('response').innerText = JSON.stringify(json, null, 2);
            }

            async function showLogs() {
                const resp = await fetch('/testcallback2/logs');
                const logs = await resp.json();
                document.getElementById('logsArea').innerText = JSON.stringify(logs, null, 2);
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/testcallback2/logs")
def get_logs():
    # Return the logs as JSON
    return logs
