"""ChatGPT-Style Web UI for Aether-CyberAgent"""
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
from rich.console import Console
import json
import os

from aether.auth import load_config
from aether.agents.yellow_patcher import YellowPatcher

console = Console()
app = FastAPI()

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aether AI</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-main: #343541;
            --bg-sidebar: #202123;
            --msg-user: #343541;
            --msg-bot: #444654;
            --text-main: #ECECF1;
            --text-muted: #8E8EA0;
            --accent: #10a37f;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: var(--bg-main); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }
        
        .sidebar { width: 260px; background-color: var(--bg-sidebar); padding: 10px; display: flex; flex-direction: column; }
        .new-chat { background-color: transparent; border: 1px solid #565869; color: white; padding: 12px; border-radius: 6px; cursor: pointer; text-align: left; display: flex; align-items: center; gap: 10px; transition: 0.2s; }
        .new-chat:hover { background-color: #2b2c2f; }
        .sidebar-bottom { margin-top: auto; border-top: 1px solid #4d4d4f; padding-top: 10px; font-size: 0.85rem; color: var(--text-muted); }
        
        .main { flex: 1; display: flex; flex-direction: column; position: relative; }
        
        .chat-container { flex: 1; overflow-y: auto; padding-bottom: 120px; }
        .message { padding: 24px; display: flex; justify-content: center; border-bottom: 1px solid rgba(32,33,35,0.5); }
        .message.bot { background-color: var(--msg-bot); }
        .message-content { max-width: 800px; width: 100%; display: flex; gap: 20px; line-height: 1.6; }
        .avatar { width: 30px; height: 30px; border-radius: 2px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }
        .avatar.user { background-color: #5436DA; }
        .avatar.bot { background-color: var(--accent); }
        
        .input-area { position: absolute; bottom: 0; width: 100%; background: linear-gradient(180deg, rgba(53,55,64,0), var(--bg-main) 40%); padding: 30px; display: flex; justify-content: center; }
        .input-box { max-width: 800px; width: 100%; position: relative; background-color: #40414F; border-radius: 10px; box-shadow: 0 0 15px rgba(0,0,0,0.1); border: 1px solid rgba(32,33,35,0.5); }
        .input-box input { width: 100%; background: transparent; border: none; color: white; padding: 16px 50px 16px 16px; font-size: 1rem; outline: none; }
        .input-box button { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 5px; font-size: 1.2rem; transition: 0.2s; }
        .input-box button:hover { color: var(--text-main); }
        
        pre { background-color: #000; padding: 15px; border-radius: 5px; overflow-x: auto; margin: 10px 0; }
        code { font-family: monospace; }
        
        .loading { display: inline-block; width: 10px; height: 10px; background-color: var(--text-main); border-radius: 50%; animation: blink 1.4s infinite both; }
        @keyframes blink { 0% { opacity: 0.2; } 20% { opacity: 1; } 100% { opacity: 0.2; } }
    </style>
</head>
<body>
    <div class="sidebar">
        <button class="new-chat" onclick="location.reload()"><i class="fa-solid fa-plus"></i> New Chat</button>
        <div class="sidebar-bottom">
            <p><i class="fa-solid fa-shield-halved"></i> Aether Web UI</p>
            <p id="model-status" style="margin-top: 10px;">Model: Loading...</p>
        </div>
    </div>
    
    <div class="main">
        <div class="chat-container" id="chat">
            <div class="message bot">
                <div class="message-content">
                    <div class="avatar bot"><i class="fa-solid fa-robot"></i></div>
                    <div>Hello! I am Aether, your autonomous AI security platform. How can I help you today?</div>
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <div class="input-box">
                <input type="text" id="userInput" placeholder="Send a message to Aether..." onkeypress="handleKey(event)">
                <button onclick="sendMessage()"><i class="fa-solid fa-paper-plane"></i></button>
            </div>
        </div>
    </div>

    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        const chat = document.getElementById('chat');
        const input = document.getElementById('userInput');
        let isWaiting = false;

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'status') {
                document.getElementById('model-status').innerText = 'Model: ' + data.model;
            } else if (data.type === 'response') {
                removeLoading();
                appendMessage('bot', data.text);
                isWaiting = false;
            } else if (data.type === 'error') {
                removeLoading();
                appendMessage('bot', 'Error: ' + data.text, true);
                isWaiting = false;
            }
        };

        function handleKey(e) {
            if (e.key === 'Enter') sendMessage();
        }

        function appendMessage(sender, text, isError = false) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${sender}`;
            
            // Basic markdown handling for code blocks
            let formattedText = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
            formattedText = formattedText.replace(/\n/g, '<br>');
            
            const color = isError ? 'color: #ff6b6b;' : '';
            
            msgDiv.innerHTML = `
                <div class="message-content">
                    <div class="avatar ${sender}">
                        ${sender === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>'}
                    </div>
                    <div style="${color}">${formattedText}</div>
                </div>
            `;
            chat.appendChild(msgDiv);
            chat.scrollTop = chat.scrollHeight;
        }

        function showLoading() {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message bot loading-msg';
            msgDiv.innerHTML = `
                <div class="message-content">
                    <div class="avatar bot"><i class="fa-solid fa-robot"></i></div>
                    <div><span class="loading"></span><span class="loading" style="animation-delay: 0.2s; margin: 0 4px;"></span><span class="loading" style="animation-delay: 0.4s;"></span></div>
                </div>
            `;
            chat.appendChild(msgDiv);
            chat.scrollTop = chat.scrollHeight;
        }

        function removeLoading() {
            const loadingMsg = document.querySelector('.loading-msg');
            if (loadingMsg) loadingMsg.remove();
        }

        function sendMessage() {
            if (!input.value.trim() || isWaiting) return;
            const text = input.value;
            appendMessage('user', text);
            input.value = '';
            showLoading();
            isWaiting = true;
            ws.send(JSON.stringify({ text: text }));
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(HTML)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    config = load_config()
    api_key = os.environ.get("GEMINI_API_KEY") or config.get("api_key", "")
    model = config.get("model", "gemini-1.5-pro-latest")
    
    await websocket.send_text(json.dumps({
        "type": "status",
        "model": model
    }))
    
    if not api_key:
        await websocket.send_text(json.dumps({
            "type": "error",
            "text": "API Key is missing. Please authenticate via the CLI first using /auth."
        }))
        return
        
    try:
        patcher = YellowPatcher(api_key=api_key, model=model)
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "text": f"Initialization error: {e}"
        }))
        return
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            user_msg = payload.get("text", "")
            
            try:
                # Build context-aware prompt using aether's prompt engine
                prompt = patcher.prompt_builder.build_chat_prompt(user_msg, "", "")
                
                # Run in separate thread
                response = await asyncio.to_thread(patcher.ai.generate_content, prompt)
                
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "text": response.text
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "text": str(e)
                }))
    except WebSocketDisconnect:
        pass

def run_server():
    console.print("[bold green]🌐 Starting Aether ChatGPT Web UI on http://localhost:8420[/bold green]")
    uvicorn.run(app, host="0.0.0.0", port=8420)
