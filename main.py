from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pyodbc
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import requests, os

app = FastAPI()

# ✅ Enable CORS to allow frontend JS to hit backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv()

# Serve static files (JS, CSS, logo, index.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

# SQL config
conn_str = (
    f'DRIVER={{ {os.getenv("AZURE_SQL_DRIVER")} }};'
    f'SERVER={os.getenv("AZURE_SQL_SERVER")};'
    f'DATABASE={os.getenv("AZURE_SQL_DATABASE")};'
    f'UID={os.getenv("AZURE_SQL_USERNAME")};'
    f'PWD={os.getenv("AZURE_SQL_PASSWORD")};'
    'Encrypt=yes;TrustServerCertificate=no;'
)
# Serve the main HTML page
@app.get("/")
def serve_homepage():
    return FileResponse("static/index.html")

# Handle login
@app.post("/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM Users WHERE Username = ? AND Password = ?", (username, password)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return {"success": True}
        else:
            return {"success": False, "message": "Invalid credentials"}

    except Exception as e:
        return {"success": False, "message": str(e)}
    

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")


class Question(BaseModel):
    question: str

@app.post("/ask")
def ask_question(payload: Question):
    question = payload.question
    try:
        # Retrieve docs from Azure Search
        search_url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX}/docs/search?api-version=2023-07-01-Preview"
        search_headers = {"api-key": AZURE_SEARCH_KEY, "Content-Type": "application/json"}
        search_payload = {"search": question, "top": 3}
        docs = requests.post(search_url, headers=search_headers, json=search_payload).json()["value"]

        # Extract `chunk` + title (fallback: content)
        documents = "\n".join(
            [f"[{doc.get('title', 'No Title')}]\n{doc.get('chunk') or doc.get('content', '')}" for doc in docs]
        )

        # Ask OpenAI
        openai_url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version=2024-03-01-preview"
        openai_headers = {"api-key": AZURE_OPENAI_KEY, "Content-Type": "application/json"}
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                    "あなたは社内ドキュメントをもとに回答するAIアシスタントです。"
                    "出力は常に **Markdown形式** で行ってください。"
                    "- 見出しには `#` を使う\n"
                    "- 太字や箇条書きを適切に使用する\n"
                    "- セクションごとに整理して分かりやすく記載してください\n"
                    "- 回答は敬語・丁寧語で記載してください\n"
                    "※ドキュメント以外の知識や想像で答えず、情報がなければ「提供された情報に記載がありません」と答えてください。"
                )
                },
                {
                    "role": "user",
                    "content": f"質問: {question}\n\n以下の情報を参考にしてください:\n{documents}",
                },
            ],
            "temperature": 0.3
        }

        gpt_answer = requests.post(openai_url, headers=openai_headers, json=payload).json()
        return { "answer": gpt_answer["choices"][0]["message"]["content"] }

    except Exception as e:
        return { "answer": f"⚠️ Error: {str(e)}" }
    


    

    
