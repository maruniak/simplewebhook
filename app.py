from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime
import urllib.parse

app = FastAPI()

# Global in-memory logs list
logs = []

@app.get("/testcallback2")
def read_test():
    logs.append({
        "method": "GET",
        "time": datetime.now().isoformat(),
        "body": None
    })
    return {"message": "GET request success"}

@app.post("/testcallback2")
async def create_test(request: Request):
    raw_body = await request.body()
    # raw_body is URL-encoded form data (bytes). Decode it and parse.
    body_str = raw_body.decode('utf-8')
    parsed_data = urllib.parse.parse_qs(body_str)

    logs.append({
        "method": "POST",
        "time": datetime.now().isoformat(),
        "body": parsed_data
    })
    return {"received_data": parsed_data}

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
                try {
                    const resp = await fetch('/webhook/testcallback2');
                    if (!resp.ok) throw new Error('Network response was not ok');
                    const json = await resp.json();
                    document.getElementById('response').innerText = JSON.stringify(json, null, 2);
                } catch (err) {
                    document.getElementById('response').innerText = "Error fetching GET data: " + err.message;
                }
            }

            async function postData() {
                try {
                    const resp = await fetch('/webhook/testcallback2', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: 'foo=bar'
                    });
                    if (!resp.ok) throw new Error('Network response was not ok');
                    const json = await resp.json();
                    document.getElementById('response').innerText = JSON.stringify(json, null, 2);
                } catch (err) {
                    document.getElementById('response').innerText = "Error posting data: " + err.message;
                }
            }

            async function showLogs() {
                try {
                    const resp = await fetch('/webhook/testcallback2/logs');
                    if (!resp.ok) throw new Error('Network response was not ok');
                    const logs = await resp.json();
                    document.getElementById('logsArea').innerText = JSON.stringify(logs, null, 2);
                } catch (err) {
                    document.getElementById('logsArea').innerText = "Error fetching logs: " + err.message;
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/testcallback2/logs")
def get_logs():
    return logs
