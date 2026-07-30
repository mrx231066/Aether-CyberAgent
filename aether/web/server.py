"""WebSocket Visualizer Sidecar for Aether-CyberAgent v2.0.0"""
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
from rich.console import Console
import json

console = Console()
app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Aether-CyberAgent Telemetry Sidecar</title>
        <style>
            body { background: #1a1b26; color: #7aa2f7; font-family: monospace; padding: 20px; }
            #messages { height: 80vh; overflow-y: scroll; border: 1px solid #7aa2f7; padding: 10px; }
        </style>
    </head>
    <body>
        <h2>🌐 Aether Telemetry Dashboard</h2>
        <div id="messages"></div>
        <script>
            var ws = new WebSocket("ws://localhost:8420/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('div');
                var content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
                messages.scrollTop = messages.scrollHeight;
            };
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    from aether.config import SessionState
    last_tokens = 0
    try:
        while True:
            await asyncio.sleep(2)
            if SessionState.total_tokens != last_tokens:
                await websocket.send_text(json.dumps({
                    "event": "metrics_update",
                    "total_tokens": SessionState.total_tokens
                }))
                last_tokens = SessionState.total_tokens
    except Exception:
        pass

def run_server():
    console.print("[bold green]🌐 Starting WebSocket Sidecar on http://localhost:8420[/bold green]")
    uvicorn.run(app, host="0.0.0.0", port=8420)
